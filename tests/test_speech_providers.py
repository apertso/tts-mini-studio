import base64
import io
import json
import re
import time
import unittest
import wave
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit

from tts.config import FISH_SPEECH_MAX_REQUEST_UTF8_BYTES
from tts.core import pcm_to_wav
from tts.runpod import runpod_handler
from tts.server import app
from tts.voices import default_voice_id, list_available_voices

FISH_VOICE_ID = default_voice_id("fish-speech")
CLOUD_VOICE_ID = default_voice_id("openrouter")


class SpeechProviderTests(unittest.TestCase):
    def setUp(self):
        self.requests = []
        self.references = [FISH_VOICE_ID]
        self.fish_audio = pcm_to_wav(b"\x00\x01" * 441, 44100)
        self.base_url = "https://fish-speech.example"
        self.enterContext(patch("tts.core.urllib.request.urlopen", side_effect=self.speech_response))
        self.fish_config = {
            "TTS_PROVIDER": "fish-speech",
            "FISH_SPEECH_BASE_URL": self.base_url + "/",
            "FISH_SPEECH_API_KEY": "test-fish-key",
            "OPENROUTER_API_KEY": "",
        }

    def speech_response(self, request, *, timeout):
        self.requests.append(request)
        path = urlsplit(request.full_url).path
        if path == "/v1/references/list":
            return io.BytesIO(json.dumps({"reference_ids": self.references}).encode())
        if path == "/v1/tts":
            return io.BytesIO(self.fish_audio)
        if path == "/api/v1/audio/speech":
            response = io.BytesIO(b"\x00\x01" * 240)
            response.headers = {"Content-Type": "audio/pcm;rate=24000;channels=1"}
            return response
        self.fail(f"Unexpected speech request to {request.full_url}")

    def test_runpod_job_uses_fish_speech_and_combines_chunks(self):
        text = "\u044f" * (FISH_SPEECH_MAX_REQUEST_UTF8_BYTES // 2 + 1)
        with patch.dict("os.environ", self.fish_config), patch("tts.runpod._build_progress_reporter") as progress:
            result = runpod_handler({"input": {"text": text, "voice_id": FISH_VOICE_ID}})

        self.assertEqual(result.get("delivery"), "inline_base64", result)
        references, first_chunk, second_chunk = self.requests
        self.assertEqual(references.full_url, self.base_url + "/v1/references/list")
        self.assertEqual(references.get_method(), "GET")
        self.assertEqual(references.headers["Accept"], "application/json")
        for request in self.requests:
            self.assertEqual(request.headers["Authorization"], "Bearer test-fish-key")

        chunks = []
        for request in (first_chunk, second_chunk):
            self.assertEqual(request.full_url, self.base_url + "/v1/tts")
            self.assertEqual(request.get_method(), "POST")
            payload = json.loads(request.data)
            chunk = payload.pop("text")
            self.assertEqual(payload, {"reference_id": FISH_VOICE_ID, "format": "wav", "streaming": False})
            self.assertLessEqual(len(chunk.encode()), FISH_SPEECH_MAX_REQUEST_UTF8_BYTES)
            chunks.append(chunk)
        self.assertEqual("".join(chunks), text)
        self.assertEqual([call.args for call in progress.return_value.call_args_list], [(1, 2), (2, 2)])

        with wave.open(io.BytesIO(base64.b64decode(result["audio_base64"])), "rb") as wav_file:
            self.assertEqual(wav_file.getframerate(), 44100)
            self.assertEqual(wav_file.getnchannels(), 1)
            self.assertEqual(wav_file.getsampwidth(), 2)
            self.assertEqual(wav_file.getnframes(), 2 * 441 + int(44100 * 0.045))

    def test_missing_reference_fails_before_synthesis(self):
        self.references = []
        with patch.dict("os.environ", self.fish_config):
            result = runpod_handler({"input": {"text": "Hello."}})
        self.assertIn(f"{FISH_VOICE_ID!r} is not registered", result.get("error", ""))
        [references] = self.requests
        self.assertEqual(references.full_url, self.base_url + "/v1/references/list")

    def test_surprise_voice_needs_no_reference(self):
        with patch.dict("os.environ", self.fish_config):
            result = runpod_handler({"input": {"text": "Hello.", "voice_id": "surprise"}})
        self.assertEqual(result.get("delivery"), "inline_base64", result)
        [request] = self.requests
        self.assertEqual(urlsplit(request.full_url).path, "/v1/tts")
        self.assertNotIn("reference_id", json.loads(request.data))

    def test_voice_catalog_follows_provider(self):
        fish_ids = [voice["id"] for voice in list_available_voices("fish-speech")]
        self.assertEqual(fish_ids[0], "en-female-1")
        self.assertIn("ru-male-1", fish_ids)
        self.assertEqual(fish_ids[-1], "surprise")
        self.assertNotIn(CLOUD_VOICE_ID, fish_ids)
        self.assertNotIn("surprise", [voice["id"] for voice in list_available_voices("openrouter")])

        with patch.dict("os.environ", self.fish_config):
            voices = app.test_client().get("/api/voices").get_json()["voices"]
            result = runpod_handler({"input": {"text": "Hello.", "voice_id": CLOUD_VOICE_ID}})
        self.assertEqual([voice["id"] for voice in voices], fish_ids)
        self.assertIn("Unknown voice_id", result.get("error", ""))
        self.assertEqual(self.requests, [])

    def test_bundled_references_match_the_catalog(self):
        root = Path(__file__).resolve().parent.parent / "assets" / "voice_references"
        for voice in list_available_voices("fish-speech"):
            if voice["id"] == "surprise":
                continue
            folder = root / voice["id"]
            self.assertTrue((folder / "sample.lab").read_text(encoding="utf-8").strip(), voice["id"])
            with wave.open(str(folder / "sample.wav"), "rb") as wav_file:
                seconds = wav_file.getnframes() / wav_file.getframerate()
                self.assertEqual((wav_file.getnchannels(), wav_file.getsampwidth()), (1, 2))
                self.assertTrue(8 <= seconds <= 30, (voice["id"], seconds))

        # The hosted frontend cannot call /api/voices, so its fallback list must match.
        constants = (root.parent.parent / "docs" / "src" / "constants.js").read_text(encoding="utf-8")
        fallback = constants.split("RUNPOD_FALLBACK_VOICES = [", 1)[1].split("];", 1)[0]
        frontend_ids = re.findall(r'id: "([^"]+)"', fallback)
        self.assertEqual(frontend_ids, [voice["id"] for voice in list_available_voices("fish-speech")])

    def test_invalid_wav_fails_the_runpod_job(self):
        self.fish_audio = self.fish_audio[:-2]
        with patch.dict("os.environ", self.fish_config):
            result = runpod_handler({"input": {"text": "Hello."}})
        self.assertIn("Fish Speech returned invalid WAV audio", result.get("error", ""))

    def read_flask_job_wav(self, config):
        with patch.dict("os.environ", config):
            client = app.test_client()
            health = client.get("/health").get_json()
            self.assertEqual(health["provider"], config["TTS_PROVIDER"])
            self.assertTrue(health["provider_configured"])
            response = client.post("/tts/jobs", json={"text": "Hello."})
            self.assertEqual(response.status_code, 202)
            job_url = f"/tts/jobs/{response.get_json()['id']}"
            deadline = time.monotonic() + 3
            while True:
                job = client.get(job_url).get_json()
                if job["status"] not in {"IN_QUEUE", "IN_PROGRESS"} or time.monotonic() >= deadline:
                    break
                time.sleep(0.01)
            self.assertEqual(job["status"], "COMPLETED", job)
            response = client.get(job_url + "/audio")
            self.assertEqual(response.mimetype, "audio/wav")
            return response.data

    def test_flask_job_can_use_fish_speech(self):
        audio = self.read_flask_job_wav(self.fish_config)
        with wave.open(io.BytesIO(audio), "rb") as wav_file:
            self.assertEqual((wav_file.getframerate(), wav_file.getnframes()), (44100, 441))

    def test_flask_job_can_still_use_openrouter(self):
        config = {"TTS_PROVIDER": "openrouter", "OPENROUTER_API_KEY": "test-openrouter-key"}
        audio = self.read_flask_job_wav(config)
        with wave.open(io.BytesIO(audio), "rb") as wav_file:
            self.assertEqual((wav_file.getframerate(), wav_file.getnframes()), (24000, 240))

        [request] = self.requests
        self.assertEqual(request.full_url, "https://openrouter.ai/api/v1/audio/speech")
        self.assertEqual(request.headers["Authorization"], "Bearer test-openrouter-key")
        payload = json.loads(request.data)
        self.assertEqual(payload["model"], "fish-audio/drama-3")
        self.assertEqual(payload["voice"], CLOUD_VOICE_ID)
        self.assertEqual(payload["response_format"], "pcm")
