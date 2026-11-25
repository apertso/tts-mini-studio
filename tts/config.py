from __future__ import annotations

import os
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

MAX_TEXT_CHARACTERS = 50_000
# shortcut: stay under Fish Drama 3's 100_000 UTF-8 byte request cap; raise if one call accepts more.
MAX_REQUEST_UTF8_BYTES = 80_000
# Bound each self-hosted WAV response and report progress during long jobs.
FISH_SPEECH_MAX_REQUEST_UTF8_BYTES = 2_000
REQUEST_TIMEOUT_SECONDS = 600

DRAMA3_MODEL = "fish-audio/drama-3"
OPENROUTER_SPEECH_URL = "https://openrouter.ai/api/v1/audio/speech"
OPENROUTER_API_KEY_ENV = "OPENROUTER_API_KEY"

DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = ("en", "ru")
ALLOWED_MODES = {"local", "runpod"}


def _load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv(BASE_DIR / ".env")

TTS_HOST = os.getenv("TTS_HOST", "0.0.0.0")
TTS_PORT = int(os.getenv("TTS_PORT", "5000"))
LOCAL_JOB_TTL_SECONDS = max(60, int(os.getenv("LOCAL_JOB_TTL_SECONDS", "3600")))
LOCAL_JOB_MAX_TERMINAL = max(10, int(os.getenv("LOCAL_JOB_MAX_TERMINAL", "200")))
MODE = (os.getenv("TTS_MODE", "local") or "local").strip().lower()


def openrouter_api_key() -> str:
    return (os.getenv(OPENROUTER_API_KEY_ENV) or "").strip()


def fish_speech_base_url() -> str:
    return os.getenv("FISH_SPEECH_BASE_URL", "").strip().rstrip("/")


def fish_speech_api_key() -> str:
    return os.getenv("FISH_SPEECH_API_KEY", "").strip()


def speech_provider() -> str:
    provider = os.getenv("TTS_PROVIDER", "openrouter").strip().lower()
    if provider not in {"openrouter", "fish-speech"}:
        raise ValueError("TTS_PROVIDER must be 'openrouter' or 'fish-speech'.")
    return provider


def speech_provider_configured(provider: str) -> bool:
    if provider == "fish-speech":
        return bool(fish_speech_base_url())
    return bool(openrouter_api_key())


def normalize_language_code(language: str | None) -> str:
    raw = (language or DEFAULT_LANGUAGE).strip().lower()
    if not raw:
        return DEFAULT_LANGUAGE

    if raw.startswith("en"):
        return "en"
    if raw.startswith("ru"):
        return "ru"

    supported = ", ".join(SUPPORTED_LANGUAGES)
    raise ValueError(
        f"Unsupported language: {language!r}. Supported languages: [{supported}]"
    )


def validate_mode(mode: str) -> str:
    normalized = (mode or "").strip().lower()
    if normalized not in ALLOWED_MODES:
        expected = ", ".join(sorted(ALLOWED_MODES))
        raise ValueError(f"Invalid TTS_MODE: {mode!r}. Expected one of: {expected}")
    return normalized


def configure_stdio() -> None:
    """Avoid Windows stdout/stderr crashes on non-ASCII log messages."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(errors="backslashreplace")
            except ValueError:
                continue
