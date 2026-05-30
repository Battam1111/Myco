// Float representation helper — shared across request encoders.
//
// Part of the bridge wire protocol (split out of the former monolithic
// `protocol/messages.ts`). The repr convention here is the wire contract for
// how floats round-trip across the Rust/Python/TS boundary; it MUST stay
// byte-identical to the Rust + Python `float_repr` helpers.

/**
 * Format a number as a Python-compatible repr string.
 *
 * Identical convention to the Rust + Python `float_repr` helpers. This is
 * how M5/M6 round-trips floats across language boundaries deterministically.
 *
 * - NaN → "nan"
 * - +Inf → "inf"
 * - -Inf → "-inf"
 * - Integer-valued and within ±1e16 → "N.0" (e.g., "0.0", "1.0", "-2.0")
 * - Otherwise → default `String(n)` (which matches Python's `repr` for most cases)
 */
export function floatRepr(n: number): string {
  if (Number.isNaN(n)) return "nan";
  if (!Number.isFinite(n)) return n > 0 ? "inf" : "-inf";
  if (Math.abs(n) < 1e16 && Math.trunc(n) === n) {
    // Integer-valued: emit "N.0" — matches Rust's `format!("{f:.1}")` and Python's repr.
    return `${n.toFixed(1)}`;
  }
  return String(n);
}
