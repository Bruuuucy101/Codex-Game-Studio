import struct
import unittest
from fixtures import wav


class PCMValidationTests(unittest.TestCase):
    def test_audio_accepts_complete_pcm_24khz_16bit_mono_or_stereo(self):
        from ccgs.voice.audio import validate_wav
        mono = validate_wav(wav(channels=1))
        stereo = validate_wav(wav(channels=2))
        self.assertEqual((mono["sample_rate"], mono["bits_per_sample"], mono["channels"]), (24000, 16, 1))
        self.assertEqual(stereo["channels"], 2)
        self.assertGreater(mono["frames"], 0)

    def test_audio_rejects_wrong_codec_rate_width_channels_and_truncation(self):
        from ccgs.voice.audio import validate_wav
        invalid = [wav(rate=22050), wav(width=1), wav(channels=3), b"ID3" + b"x" * 100, wav()[:-1]]
        compressed = bytearray(wav()); compressed[20:22] = struct.pack("<H", 3); invalid.append(bytes(compressed))
        for raw in invalid:
            with self.subTest(prefix=raw[:12]):
                with self.assertRaises(ValueError): validate_wav(raw)

    def test_audio_rejects_incomplete_frames_zero_frames_and_declared_oversize(self):
        from ccgs.voice.audio import validate_wav
        zero = wav(frames=1)[:-2] + b""
        malformed = bytearray(wav()); malformed[40:44] = struct.pack("<I", 2**26 + 1)
        for raw in (zero, bytes(malformed)):
            with self.assertRaises(ValueError): validate_wav(raw)

    def test_audio_rejects_data_chunk_before_format_chunk(self):
        from ccgs.voice.audio import validate_wav
        raw = wav()
        self.assertEqual(raw[12:16], b"fmt ")
        self.assertEqual(raw[36:40], b"data")
        reordered = raw[:12] + raw[36:] + raw[12:36]
        with self.assertRaisesRegex(ValueError, "data_before_format"):
            validate_wav(reordered)
