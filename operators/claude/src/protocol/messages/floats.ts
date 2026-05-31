// Float representation helper — shared across request encoders.
//
// Part of the bridge wire protocol (split out of the former monolithic
// `protocol/messages.ts`). The repr convention here is the wire contract for
// how floats round-trip across the Rust/Python/TS boundary; it MUST stay
// byte-identical to the Rust (kernel/shared::float_repr) and Python (bare
// builtin `repr`) renderings.

/**
 * Format a number as the exact CPython `repr(float)` of its f64 value — the
 * canonical-bytes wire form for a float.
 *
 * ## Why floats are strings
 *
 * The canonical-bytes serializer has no float tag; floats are encoded as
 * `String(floatRepr(x))` (a tag-0x20 String). A raw IEEE-754 encoding has
 * cross-language reproducibility hazards (NaN payload bits, signaling bits,
 * significand endianness); round-tripping through the shortest decimal string
 * that recovers the same f64 sidesteps all of it.
 *
 * ## The oracle
 *
 * The original producer is the Python kernel calling the builtin `repr()`.
 * **CPython `repr(float)` is therefore the canonical oracle**, and this function
 * reproduces it byte-for-byte. Divergence from it is the float facet of
 * L1/HARD_RULES C18 `canonical_bytes_render_drift` (CRITICAL). Cross-language
 * parity is pinned by the `float_vectors` array in
 * `test_vectors/canonical_bytes_v1.json`.
 *
 * ## The rules (= CPython repr)
 *
 * `repr(float)` is the shortest decimal string that round-trips to the same f64
 * under round-to-nearest-**even**, formatted as:
 *
 * - exponential iff the decimal exponent `x` (value `d.ddd x 10^x`) satisfies
 *   `x < -4` or `x >= 16`; otherwise positional;
 * - integer-valued positional gets a trailing `.0` (`1.0`, `100.0`);
 * - exponential uses `e`, an always-present sign (`e+` / `e-`), and an exponent
 *   zero-padded to at least 2 digits (`1e-05`, `1e+16`, `1.5e+300`);
 * - `-0.0` keeps its sign;
 * - non-finite: `nan`, `inf`, `-inf` (rejected as divergence upstream, branch
 *   pinned here).
 *
 * ## Why this is not just `String(n)` / `toExponential`
 *
 * JavaScript's `Number.prototype.toString` switches to exponential at different
 * thresholds than CPython (and never zero-pads exponents), and the old
 * implementation also dropped the sign of `-0.0`. We instead build the digits
 * from `toExponential(p)` at the shortest round-tripping precision, then apply
 * CPython's notation rules. One extra wrinkle: `toExponential(p)` breaks exact
 * midpoint ties by rounding **half-away**, whereas CPython rounds
 * **half-to-even** — so we detect exact midpoint ties with exact BigInt
 * arithmetic and pick the even last digit, matching CPython on every f64.
 */
export function floatRepr(n: number): string {
  if (Number.isNaN(n)) return "nan";
  if (!Number.isFinite(n)) return n > 0 ? "inf" : "-inf";
  // Capture the sign via Object.is so -0 is distinguishable from +0
  // (n < 0 is false for -0).
  const negative = n < 0 || Object.is(n, -0);
  const abs = Math.abs(n);
  if (abs === 0) return negative ? "-0.0" : "0.0";

  const [digits, exp] = shortestRoundToEvenDigits(abs);
  const body = exp < -4 || exp >= 16
    ? renderExponential(digits, exp)
    : renderPositional(digits, exp);
  return negative ? "-" + body : body;
}

/**
 * Return `[digits, exp]` where `digits` is the shortest run of significant
 * decimal digits (no point, no leading zeros, trailing zeros stripped) that
 * round-trips to `abs`, and `exp` is the power of ten of the leading digit
 * (`abs === digits[0].digits[1..] x 10^exp`). Matches CPython's round-to-even
 * tie-break.
 *
 * `abs` must be finite and strictly positive.
 */
function shortestRoundToEvenDigits(abs: number): [string, number] {
  // Smallest precision whose rendering recovers `abs`. toExponential(p) rounds
  // half-away; we correct ties below. 17 significant digits always suffice.
  let p = 0;
  for (; p <= 17; p++) {
    if (Number(abs.toExponential(p)) === abs) break;
  }
  const [digHigh, exp] = parseScientific(abs.toExponential(Math.min(p, 17)));

  // Tie correction: the only way toExponential can disagree with CPython is by
  // rounding an exact midpoint up. Form the candidate one ULP-of-last-digit
  // below; if it ALSO round-trips AND the value is exactly equidistant between
  // the two, CPython would have chosen whichever last digit is even.
  const digLow = decrementLastDigit(digHigh);
  if (digLow !== null && Number(reparse(digLow, exp)) === abs) {
    if (isExactDecimalMidpoint(abs, digLow, digHigh, exp)) {
      const lastHigh = digHigh.charCodeAt(digHigh.length - 1) - 48;
      if (lastHigh % 2 === 1) {
        // digHigh is odd -> digLow is the even neighbor; CPython picks it.
        return stripTrailingZeros(digLow, exp);
      }
    }
  }
  return stripTrailingZeros(digHigh, exp);
}

/**
 * Split a `toExponential()` string (`"D"` or `"D.FFF"`, then `e`, then a signed
 * integer exponent) into significant digits (decimal point removed) and the
 * exponent of the leading digit. Trailing zeros are NOT stripped here.
 */
function parseScientific(s: string): [string, number] {
  const eIdx = s.indexOf("e");
  const mantissa = s.slice(0, eIdx);
  const exp = parseInt(s.slice(eIdx + 1), 10);
  const dotIdx = mantissa.indexOf(".");
  const digits = dotIdx === -1
    ? mantissa
    : mantissa.slice(0, dotIdx) + mantissa.slice(dotIdx + 1);
  return [digits, exp];
}

/** Strip trailing zeros from the significant digits (keep at least one). */
function stripTrailingZeros(digits: string, exp: number): [string, number] {
  let d = digits;
  while (d.length > 1 && d.endsWith("0")) d = d.slice(0, -1);
  return [d, exp];
}

/**
 * Decrement the integer formed by `digits` by 1, keeping the same length. The
 * two candidate decimals at a midpoint tie have the same number of significant
 * digits, so a borrow past the front (length change) or a resulting leading
 * zero (different magnitude) means it is NOT a same-length tie -> return null.
 */
function decrementLastDigit(digits: string): string | null {
  const arr = digits.split("");
  let i = arr.length - 1;
  while (i >= 0) {
    if (arr[i] === "0") {
      arr[i] = "9";
      i--;
    } else {
      arr[i] = String(arr[i].charCodeAt(0) - 48 - 1);
      break;
    }
  }
  if (i < 0) return null; // borrowed past the front
  const res = arr.join("");
  if (res.length !== digits.length || res[0] === "0") return null;
  return res;
}

/** Reconstruct the f64 of `digits[0].digits[1..] x 10^exp`. */
function reparse(digits: string, exp: number): number {
  const lit = digits.length === 1
    ? `${digits}e${exp}`
    : `${digits[0]}.${digits.slice(1)}e${exp}`;
  return Number(lit);
}

/**
 * Exact test: is `abs` (an f64) exactly equidistant between the two decimals
 * `Dlow = digLow x 10^k` and `Dhigh = digHigh x 10^k` (where `k = exp - (ndig-1)`
 * and `digHigh = digLow + 1` in the last place)? Equivalent to
 * `2 * abs === Dlow + Dhigh`, evaluated with exact BigInt arithmetic (no
 * floating-point rounding) by decomposing `abs` into its dyadic value
 * `M * 2^E2` and cross-multiplying out all negative powers of two and ten.
 */
function isExactDecimalMidpoint(
  abs: number,
  digLow: string,
  digHigh: string,
  exp: number,
): boolean {
  const ndig = digHigh.length;
  const k = exp - (ndig - 1); // value = intDigits * 10^k
  const sumN = BigInt(digLow) + BigInt(digHigh); // Dlow + Dhigh = sumN * 10^k

  const [M, e2] = exactDyadic(abs); // abs = M * 2^e2

  // Compare A := 2*abs = M * 2^(e2+1)  vs  B := sumN * 10^k = sumN * 2^k * 5^k.
  let A = M;
  let B = sumN;
  let aPow2 = e2 + 1;
  let bPow2 = k;
  // Clear the 5^k factor: if k >= 0 multiply B by 5^k, else multiply A by 5^(-k)
  // (multiplying the opposite side clears the denominator).
  if (k >= 0) {
    B *= 5n ** BigInt(k);
  } else {
    A *= 5n ** BigInt(-k);
  }
  // Normalize powers of two by factoring out the smaller exponent, then apply
  // the remainder to the appropriate side. Both remainders are >= 0.
  const minPow2 = Math.min(aPow2, bPow2);
  aPow2 -= minPow2;
  bPow2 -= minPow2;
  if (aPow2 > 0) A *= 1n << BigInt(aPow2);
  if (bPow2 > 0) B *= 1n << BigInt(bPow2);
  return A === B;
}

/**
 * Decompose a positive finite f64 into `[M, E2]` such that the value equals
 * `M * 2^E2` exactly, with `M` a positive BigInt.
 */
function exactDyadic(abs: number): [bigint, number] {
  const buf = new ArrayBuffer(8);
  const dv = new DataView(buf);
  dv.setFloat64(0, abs, false); // big-endian
  const hi = BigInt(dv.getUint32(0, false));
  const lo = BigInt(dv.getUint32(4, false));
  const bits = (hi << 32n) | lo;
  const expBits = Number((bits >> 52n) & 0x7ffn);
  const frac = bits & 0xfffffffffffffn;
  if (expBits === 0) {
    // subnormal: value = frac * 2^(-1074)
    return [frac, -1074];
  }
  // normal: value = (2^52 + frac) * 2^(expBits - 1075)
  return [(1n << 52n) | frac, expBits - 1075];
}

/**
 * Positional/fixed rendering. `digits` are significant digits (no point, no
 * leading zeros); `exp` is the power of ten of the leading digit. Caller
 * guarantees `-4 <= exp < 16`.
 */
function renderPositional(digits: string, exp: number): string {
  const ndigits = digits.length;
  if (exp >= 0) {
    const intLen = exp + 1;
    if (ndigits <= intLen) {
      return digits + "0".repeat(intLen - ndigits) + ".0";
    }
    return digits.slice(0, intLen) + "." + digits.slice(intLen);
  }
  return "0." + "0".repeat(-exp - 1) + digits;
}

/**
 * Exponential rendering, CPython style:
 * `first-digit[.rest]e<sign><>=2-digit exponent>`.
 */
function renderExponential(digits: string, exp: number): string {
  const first = digits.slice(0, 1);
  const rest = digits.slice(1);
  let s = first;
  if (rest.length > 0) s += "." + rest;
  s += "e";
  s += exp < 0 ? "-" : "+";
  const absExp = Math.abs(exp);
  s += absExp < 10 ? "0" + absExp : String(absExp);
  return s;
}
