"""Strict bounded RIFF/WAVE PCM validation for collected NPC dialogue."""
import struct

from ..assets.request import fail, sha256

WAV_LIMIT = 64 * 1024 * 1024
MAX_SECONDS = 10 * 60


def validate_wav(raw):
    """Return exact PCM properties for a complete 24 kHz, 16-bit mono/stereo WAV."""
    if not isinstance(raw, bytes) or not 44 <= len(raw) <= WAV_LIMIT:
        fail("invalid_wav_size")
    if raw[:4] != b"RIFF" or raw[8:12] != b"WAVE":
        fail("invalid_wav_header")
    if struct.unpack_from("<I", raw, 4)[0] + 8 != len(raw):
        fail("truncated_or_trailing_wav")
    offset = 12
    fmt = None
    data = None
    while offset < len(raw):
        if offset + 8 > len(raw):
            fail("truncated_wav_chunk")
        kind = raw[offset:offset + 4]
        size = struct.unpack_from("<I", raw, offset + 4)[0]
        start = offset + 8
        end = start + size
        padded = end + (size & 1)
        if end > len(raw) or padded > len(raw):
            fail("truncated_wav_chunk")
        if kind == b"fmt ":
            if fmt is not None or size < 16:
                fail("invalid_wav_format_chunk")
            fmt = raw[start:end]
        elif kind == b"data":
            if fmt is None:
                fail("wav_data_before_format")
            if data is not None:
                fail("duplicate_wav_data")
            data = raw[start:end]
        offset = padded
    if offset != len(raw) or fmt is None or data is None:
        fail("missing_wav_chunk")
    codec, channels, rate, byte_rate, block_align, bits = struct.unpack_from("<HHIIHH", fmt)
    if codec != 1:
        fail("wav_must_be_pcm")
    if channels not in (1, 2) or rate != 24000 or bits != 16:
        fail("unsupported_pcm_properties")
    expected_align = channels * 2
    if block_align != expected_align or byte_rate != rate * expected_align:
        fail("invalid_pcm_alignment")
    if not data or len(data) % block_align:
        fail("incomplete_pcm_frames")
    frames = len(data) // block_align
    if frames > rate * MAX_SECONDS:
        fail("wav_duration_limit")
    return {"format": "wav", "codec": "pcm", "sample_rate": rate,
            "bits_per_sample": bits, "channels": channels, "frames": frames,
            "duration_seconds": frames / rate, "size": len(raw), "sha256": sha256(raw)}
