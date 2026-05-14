// Stdio framing — TypeScript implementation.
//
// Frame format mirrors Rust `kernel/bridge/src/framing.rs` and Python
// `kernel/bridge_python/src/myco_kernel_bridge/framing.py`:
//
// ```
//   [u32 BE length, 4 bytes][frame body, length bytes]
// ```

import {
  FrameTooLargeError,
  MAX_FRAME_BODY_SIZE,
} from "./messages.ts";

/**
 * Pull `n` bytes from the front of a queue of buffers.
 *
 * Returns `null` if the queue does not have enough bytes yet (and leaves
 * the queue unchanged). Returns a fresh Uint8Array of exactly `n` bytes
 * otherwise, mutating the queue to drop those bytes.
 */
function pullBytes(queue: Uint8Array[], n: number): Uint8Array | null {
  let total = 0;
  for (const chunk of queue) total += chunk.length;
  if (total < n) return null;

  const out = new Uint8Array(n);
  let written = 0;
  while (written < n) {
    const head = queue[0]!;
    const need = n - written;
    if (head.length <= need) {
      out.set(head, written);
      written += head.length;
      queue.shift();
    } else {
      out.set(head.subarray(0, need), written);
      queue[0] = head.subarray(need);
      written += need;
    }
  }
  return out;
}

/**
 * Frame reader — accumulates raw bytes from a streaming source (e.g., a
 * subprocess's stdout) and yields complete frame bodies (HMAC + body)
 * when they're available.
 *
 * Usage:
 *
 * ```ts
 *   const reader = new FrameReader();
 *   stream.on('data', (chunk) => {
 *     reader.push(chunk);
 *     while (true) {
 *       const frame = reader.tryReadFrame();
 *       if (!frame) break;
 *       // process frame
 *     }
 *   });
 * ```
 */
export class FrameReader {
  private queue: Uint8Array[] = [];

  /** Feed incoming bytes from the stream. */
  push(chunk: Uint8Array): void {
    if (chunk.length > 0) {
      this.queue.push(chunk);
    }
  }

  /**
   * Try to extract one complete frame body from the queue.
   *
   * Returns `null` if not enough bytes are buffered yet. Throws on
   * oversized frame. Mutates the queue to consume the frame's bytes on
   * success.
   */
  tryReadFrame(): Uint8Array | null {
    const lengthBytes = pullBytes(this.queue, 4);
    if (lengthBytes === null) return null;
    const length =
      (lengthBytes[0]! << 24) |
      (lengthBytes[1]! << 16) |
      (lengthBytes[2]! << 8) |
      lengthBytes[3]!;
    if (length > MAX_FRAME_BODY_SIZE) {
      throw new FrameTooLargeError(
        `incoming frame size ${length} exceeds cap ${MAX_FRAME_BODY_SIZE}`,
      );
    }
    const body = pullBytes(this.queue, length);
    if (body === null) {
      // Not enough bytes for the body yet — push the length prefix back.
      // We need to be careful: pullBytes already consumed the length bytes.
      // Reconstruct the length-prefix as a chunk at the head of the queue.
      const lp = new Uint8Array(4);
      lp[0] = lengthBytes[0]!;
      lp[1] = lengthBytes[1]!;
      lp[2] = lengthBytes[2]!;
      lp[3] = lengthBytes[3]!;
      this.queue.unshift(lp);
      return null;
    }
    return body;
  }

  /** Whether the queue is empty (no buffered bytes). */
  isEmpty(): boolean {
    return this.queue.length === 0;
  }
}

/**
 * Encode a frame for writing: length-prefix (u32 BE) + body.
 *
 * Returns a Uint8Array ready to be written to a stream.
 */
export function encodeFrame(body: Uint8Array): Uint8Array {
  if (body.length > MAX_FRAME_BODY_SIZE) {
    throw new FrameTooLargeError(
      `outgoing frame size ${body.length} exceeds cap ${MAX_FRAME_BODY_SIZE}`,
    );
  }
  const out = new Uint8Array(4 + body.length);
  out[0] = (body.length >>> 24) & 0xff;
  out[1] = (body.length >>> 16) & 0xff;
  out[2] = (body.length >>> 8) & 0xff;
  out[3] = body.length & 0xff;
  out.set(body, 4);
  return out;
}
