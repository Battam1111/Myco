"""Adapter for audio files via OpenAI Whisper (segment-level transcripts).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/ingestion.md``
§ "Adapters". Realises L0 P2 (永恒吞噬) for the **audio modality**:
v0.7.10's gap analysis explicitly named audio as a missing modality.
A user pointing ``myco eat --path lecture.mp3`` at a 60-minute talk
got either silent rejection (no extension match) or — worse — a
binary-rejected silent skip via the text-file NUL-byte heuristic.

This is the v0.8.0 11th adapter (1st of three multimedia adapters
gated behind the opt-in ``[multimedia]`` extras). One
:class:`IngestResult` per detected speaker turn (Whisper segment),
so downstream digestion can score, quote, or branch on a single
spoken passage rather than a one-hour blob.

Detection is extension-only:

* ``.wav``, ``.mp3``, ``.flac``, ``.m4a``, ``.ogg`` are claimed.

Architecture — **import-on-demand**:

The Whisper / PyTorch transitive closure is ~500 MB of model
weights and CUDA shared objects. Module-level imports stay stdlib-
only so ``from myco.ingestion.adapters.audio import AudioAdapter``
works on a default ``pip install myco`` install (no extras).
``ingest()`` performs the heavy import inside a ``try/except
ImportError`` block; on missing dep the adapter returns a single
failed-stub guiding the operator to ``pip install
'myco[multimedia]'`` — never silently drops the file. ``can_handle``
remains stdlib-pure: it claims by extension, then ``ingest`` either
transcribes or emits the install-extras stub. This is exactly the
shape v0.7.3's AD1 closure mandates and the v0.8.0 multimedia craft
re-affirms.

Security posture mirrors :mod:`text_file` and :mod:`sqlite`:

* **Credential-glob denial.** Reuses
  :func:`text_file._is_credential_file`. An attacker who renames
  ``id_rsa`` to ``id_rsa.wav`` cannot exfiltrate via ``myco eat``.
* **Size cap.** Files over :data:`DEFAULT_MAX_AUDIO_BYTES` (100 MB)
  are rejected by ``can_handle``; an attacker-planted multi-GB
  audio fixture cannot be used as an OOM oracle on the decoder.
  100 MB is the per-modality cap — larger than the cross-adapter
  10 MB cap because audio files are larger by nature, but smaller
  than video to keep the model warm-up bounded.
* **Failed-stub on every former silent-skip path.** Whisper
  missing, file too large, codec/decode error, model load failure
  — all produce a single failed-stub IngestResult with a concrete
  failure_reason naming the cause. Never ``[]`` (AD1).
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .protocol import Adapter, IngestResult
from .text_file import _is_credential_file

#: Size ceiling for a single audio file (100 MB). Larger than the
#: cross-adapter 10 MB cap because lossy audio of meaningful length
#: easily exceeds 10 MB; smaller than video (500 MB) to keep the
#: decode + model-warm-up bounded.
DEFAULT_MAX_AUDIO_BYTES: int = 100 * 1024 * 1024

#: File extensions claimed by this adapter. Aligned with the formats
#: ``ffmpeg`` (Whisper's transitive decoder) handles natively.
_AUDIO_EXTS: frozenset[str] = frozenset({".wav", ".mp3", ".flac", ".m4a", ".ogg"})

#: Default Whisper model name. ``base`` is the right balance of
#: accuracy and download size (~140 MB) for first-time users; power
#: users wanting better accuracy can swap to ``small`` / ``medium``
#: / ``large`` by editing this constant in a substrate-local plugin.
_DEFAULT_WHISPER_MODEL: str = "base"

#: Default speaker label. Whisper does not perform speaker
#: diarization out of the box (that needs pyannote-audio, which is
#: a separate optional dep). We surface every segment under this
#: label so downstream consumers can re-tag if a diarization pass
#: lands in v0.9+.
_DEFAULT_SPEAKER_LABEL: str = "speaker"

#: Reason text fragment for missing whisper. The exact phrasing is
#: pinned in tests so the operator-facing guidance stays stable.
_INSTALL_EXTRAS_HINT: str = (
    "myco[multimedia] not installed; run "
    "`pip install 'myco[multimedia]'` to enable audio ingestion."
)


def _posix(p: Path) -> str:
    """Normalise ``p.resolve()`` to POSIX separators (Lens 10 P1-C)."""
    return str(p.resolve()).replace("\\", "/")


def _failed_stub(
    *,
    title: str,
    source: str,
    reason: str,
    metadata: dict[str, Any] | None = None,
) -> IngestResult:
    """Construct a v0.7.3 AD1-closure failed-stub IngestResult.

    Centralised so every failure path emits the identical shape; AD1
    watches for the empty-list-return anti-pattern in adapter code, and
    concentrating the stub construction here keeps the per-failure
    call sites uniform.
    """
    return IngestResult(
        title=title,
        body="",
        source=source,
        status="failed",
        failure_reason=reason,
        metadata=metadata or {},
    )


class AudioAdapter(Adapter):
    """Adapter for audio files via OpenAI Whisper.

    Emits one :class:`IngestResult` per Whisper-detected segment.
    Each result's ``metadata`` carries:

    * ``kind`` — always ``"audio-transcript-segment"``
    * ``start_sec`` — float; segment start time
    * ``end_sec`` — float; segment end time
    * ``speaker_label`` — string; default :data:`_DEFAULT_SPEAKER_LABEL`
      (Whisper itself does not diarize)
    * ``segment_index`` — 0-based ordinal within the file
    * ``source_file`` — POSIX-normalised absolute path

    Refuses files matched by
    :data:`text_file._CREDENTIAL_DENY_GLOBS` and files over
    :data:`DEFAULT_MAX_AUDIO_BYTES` (100 MB) at ``can_handle``.
    Returns a single failed-stub on every former silent-skip path
    (whisper not installed, file too large, decode error, model
    load failure) per the v0.7.3 AD1-closure protocol.
    """

    @property
    def name(self) -> str:
        return "audio"

    @property
    def extensions(self) -> frozenset[str]:
        return _AUDIO_EXTS

    def can_handle(self, target: str) -> bool:
        """Claim by extension only; never imports whisper.

        The lazy-import architecture means ``can_handle`` must work
        without the heavy deps. We claim ``.wav``/``.mp3``/etc by
        extension, then ``ingest`` either transcribes or emits the
        install-extras failed-stub. This routes the file to the
        right adapter even on a default install, so the user gets
        clear guidance instead of the file being silently picked
        up by text-file's NUL-byte fallback (which would reject it
        with no diagnostic).
        """
        p = Path(target)
        if not p.is_file():
            return False
        if p.suffix.lower() not in _AUDIO_EXTS:
            return False
        # P0-SEC-4 parity with text_file: refuse credential-bearing
        # filenames regardless of extension. ``id_rsa.wav`` is
        # contrived but the precedent (chat_log v0.7.5) is uniform.
        if _is_credential_file(p.name):
            return False
        try:
            if p.stat().st_size > DEFAULT_MAX_AUDIO_BYTES:
                return False
        except OSError:
            return False
        return True

    def ingest(self, target: str) -> Sequence[IngestResult]:
        p = Path(target)
        # Belt + suspenders: re-check size cap and credential name at
        # ingest. ``can_handle`` may be bypassed by a third-party
        # orchestrator or test fixture calling ``ingest`` directly.
        try:
            size = p.stat().st_size
        except OSError as exc:
            return [
                _failed_stub(
                    title=p.stem,
                    source=str(p),
                    reason=f"stat() failed: {exc}",
                )
            ]
        if size > DEFAULT_MAX_AUDIO_BYTES:
            return [
                _failed_stub(
                    title=p.stem,
                    source=str(p),
                    reason=(
                        f"audio size cap exceeded: {size} > "
                        f"{DEFAULT_MAX_AUDIO_BYTES} bytes"
                    ),
                )
            ]
        if _is_credential_file(p.name):
            return [
                _failed_stub(
                    title=p.stem,
                    source=str(p),
                    reason=(f"refused credential-bearing file by name: {p.name!r}"),
                )
            ]
        # Lazy-import whisper inside ingest() so module import stays
        # stdlib-only on default installs. ImportError → install-
        # extras failed-stub; the operator gets a concrete fix.
        try:
            import whisper
        except ImportError:
            return [
                _failed_stub(
                    title=p.stem,
                    source=_posix(p),
                    reason=_INSTALL_EXTRAS_HINT,
                )
            ]
        source = _posix(p)
        # Model load can fail on disk-full / network-unreachable
        # (first-run download) / corrupt cache. Catch broadly so the
        # raised cause becomes a failed-stub instead of crashing the
        # whole eat() call.
        try:
            model = whisper.load_model(_DEFAULT_WHISPER_MODEL)
        except (OSError, RuntimeError, ValueError) as exc:
            return [
                _failed_stub(
                    title=p.stem,
                    source=source,
                    reason=(
                        f"whisper model load failed ({_DEFAULT_WHISPER_MODEL!r}): {exc}"
                    ),
                )
            ]
        # Transcription itself can fail on unsupported codecs (no
        # ffmpeg / corrupt audio / sample-rate mismatch) — same
        # story: failed-stub, never raise.
        try:
            transcription = model.transcribe(str(p))
        except (OSError, RuntimeError, ValueError) as exc:
            return [
                _failed_stub(
                    title=p.stem,
                    source=source,
                    reason=f"whisper transcription failed: {exc}",
                )
            ]
        # Whisper returns a dict with a ``segments`` list; each
        # segment is a dict with ``start``, ``end``, ``text`` keys.
        # Defensive against malformed return shapes.
        if not isinstance(transcription, dict):
            return [
                _failed_stub(
                    title=p.stem,
                    source=source,
                    reason=(
                        f"whisper returned unexpected shape: "
                        f"{type(transcription).__name__}"
                    ),
                )
            ]
        segments = transcription.get("segments")
        if not isinstance(segments, list) or not segments:
            return [
                _failed_stub(
                    title=p.stem,
                    source=source,
                    reason=(
                        f"whisper produced no segments for {p.name!r} — "
                        "audio may be silent or below detection threshold"
                    ),
                )
            ]
        results: list[IngestResult] = []
        for seg_index, seg in enumerate(segments):
            if not isinstance(seg, dict):
                # Malformed segment shape; emit a per-segment failed-
                # stub rather than dropping silently. The AD1 contract
                # is "loud about every gap"; per-segment loud-fail is
                # the right grain.
                results.append(
                    _failed_stub(
                        title=f"{p.stem}-segment-{seg_index:04d}",
                        source=source,
                        reason=(
                            f"whisper segment {seg_index} malformed: "
                            f"{type(seg).__name__}"
                        ),
                        metadata={
                            "kind": "audio-transcript-segment",
                            "segment_index": seg_index,
                            "source_file": source,
                        },
                    )
                )
                continue
            text = str(seg.get("text") or "").strip()
            if not text:
                # An empty-text segment is signal noise (Whisper
                # sometimes emits zero-content segments at silence
                # boundaries). Skip in-place by emitting a per-
                # segment failed-stub with a metadata-only marker
                # rather than ``return []``-ing or silently dropping.
                results.append(
                    _failed_stub(
                        title=f"{p.stem}-segment-{seg_index:04d}",
                        source=source,
                        reason=(
                            f"whisper segment {seg_index} produced "
                            f"empty transcript text"
                        ),
                        metadata={
                            "kind": "audio-transcript-segment-empty",
                            "segment_index": seg_index,
                            "source_file": source,
                        },
                    )
                )
                continue
            try:
                start_sec = float(seg.get("start", 0.0))
                end_sec = float(seg.get("end", 0.0))
            except (TypeError, ValueError):
                start_sec = 0.0
                end_sec = 0.0
            results.append(
                IngestResult(
                    title=f"{p.stem}-segment-{seg_index:04d}",
                    body=text,
                    tags=["audio", "audio-transcript", "transcript-segment"],
                    source=source,
                    metadata={
                        "kind": "audio-transcript-segment",
                        "start_sec": start_sec,
                        "end_sec": end_sec,
                        "speaker_label": _DEFAULT_SPEAKER_LABEL,
                        "segment_index": seg_index,
                        "source_file": source,
                    },
                )
            )
        return results
