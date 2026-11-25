import unittest
from unittest.mock import patch

from tts.config import MAX_REQUEST_UTF8_BYTES, MAX_TEXT_CHARACTERS
from tts.core import (
    classify_text_language,
    generate_tts,
    normalize_pcm,
    parse_pcm_content_type,
    pcm_to_wav,
    split_text,
)
from tts.server import app


class SpeechTextTests(unittest.TestCase):
    def test_language_classification(self):
        self.assertEqual(classify_text_language("Hello, world."), "en")
        self.assertEqual(classify_text_language("Привет, мир."), "ru")
        self.assertEqual(classify_text_language("Hello, привет."), "mixed")
        with self.assertRaises(ValueError):
            classify_text_language("Hello 你好")

    def test_byte_chunks_cover_the_symbol_limit(self):
        russian = "я" * MAX_TEXT_CHARACTERS
        chunks = split_text(russian, max_bytes=MAX_REQUEST_UTF8_BYTES)
        self.assertGreater(len(chunks), 1)
        self.assertEqual("".join(chunks), russian)
        for chunk in chunks:
            self.assertLessEqual(len(chunk.encode("utf-8")), MAX_REQUEST_UTF8_BYTES)

        english = "Hello. " * 20
        self.assertEqual(split_text(english.strip(), max_bytes=MAX_REQUEST_UTF8_BYTES), [english.strip()])

    def test_pcm_wav_roundtrip(self):
        rate, channels = parse_pcm_content_type("audio/pcm;rate=44100;channels=2")
        self.assertEqual((rate, channels), (44100, 2))
        self.assertEqual(parse_pcm_content_type("audio/pcm"), (24000, 1))

        stereo = b"\x00\x00\x02\x00" * 4
        mono = normalize_pcm(stereo, 2)
        self.assertEqual(len(mono), 8)
        wav_bytes = pcm_to_wav(mono, 44100)
        self.assertTrue(wav_bytes.startswith(b"RIFF"))
        import io
        import wave

        with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
            self.assertEqual(wav_file.getframerate(), 44100)
            self.assertEqual(wav_file.getnchannels(), 1)
            self.assertEqual(wav_file.getnframes(), 4)

    def test_job_api_rejects_other_scripts_and_missing_key(self):
        from tts.server import _validate_job_payload

        client = app.test_client()
        health = client.get("/health").get_json()
        self.assertEqual(health["model"], "fish-audio/drama-3")
        self.assertEqual(health["supported_languages"], ["en", "ru"])

        payload, error = _validate_job_payload({"text": "你好", "language": "en"})
        self.assertIsNone(payload)
        self.assertIn("English and Russian", error)

        payload, error = _validate_job_payload({
            "text": "Привет.",
            "language": "ru",
            "voice_id": "b871e425b6c0442baa5cf73f6c336bbe",
        })
        self.assertIsNone(error)
        self.assertEqual(payload["language"], "ru")

        rejected = client.post("/tts/jobs", json={"text": "你好", "language": "en"})
        self.assertEqual(rejected.status_code, 400)

        with patch.dict("os.environ", {"TTS_PROVIDER": "openrouter", "OPENROUTER_API_KEY": ""}):
            with self.assertRaises(RuntimeError) as caught:
                generate_tts("Hello.", voice_id="bf322df2096a46f18c579d0baa36f41d")
            self.assertIn("OPENROUTER_API_KEY", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
