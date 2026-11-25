from __future__ import annotations

import array
import io
import json
import re
import sys
import threading
import unicodedata
import urllib.error
import urllib.request
import wave
from typing import Callable, Iterator, List, Optional
from urllib.parse import urlsplit

from .config import (
    DRAMA3_MODEL,
    FISH_SPEECH_MAX_REQUEST_UTF8_BYTES,
    MAX_REQUEST_UTF8_BYTES,
    MAX_TEXT_CHARACTERS,
    OPENROUTER_SPEECH_URL,
    REQUEST_TIMEOUT_SECONDS,
    fish_speech_api_key,
    fish_speech_base_url,
    normalize_language_code,
    openrouter_api_key,
    speech_provider,
)
from .voices import resolve_voice


SENTENCE_SPLIT_PATTERN = re.compile("(?<=[.!?\u2026])\\s+")
SPLIT_HINT_PATTERN = re.compile(r"[,;:)\]\-]\s+|\s+")
PCM_RATE_PATTERN = re.compile(r"(?:^|;)\s*rate\s*=\s*(\d+)", re.IGNORECASE)
PCM_CHANNELS_PATTERN = re.compile(r"(?:^|;)\s*channels\s*=\s*(\d+)", re.IGNORECASE)

DEFAULT_PCM_RATE = 24000
DEFAULT_PCM_CHANNELS = 1
EDGE_FADE_MS = 8
INTER_CHUNK_PAUSE_MS = 45

ProgressCallback = Callable[[int, int], None]


class GenerationCancelledError(RuntimeError):
    """Raised when generation is cancelled via cooperative cancellation signal."""


def format_log_preview(text: str, limit: int = 50) -> str:
    preview = text[:limit]
    if len(text) > limit:
        preview += "..."
    return preview.encode("ascii", errors="backslashreplace").decode("ascii")


def classify_text_language(text: str) -> str:
    """Return en, ru, or mixed. Reject letters outside Latin and Cyrillic.

    shortcut: other Latin-script languages are allowed; add a language id to block them.
    """
    has_latin = False
    has_cyrillic = False
    for char in text:
        if not char.isalpha():
            continue
        name = unicodedata.name(char, "")
        if name.startswith("LATIN "):
            has_latin = True
        elif name.startswith("CYRILLIC "):
            has_cyrillic = True
        else:
            raise ValueError("Only English and Russian text is supported.")

    if has_cyrillic and not has_latin:
        return "ru"
    if has_latin and not has_cyrillic:
        return "en"
    return "mixed"


def _utf8_len(text: str) -> int:
    return len(text.encode("utf-8"))


def _window_within_bytes(text: str, max_bytes: int) -> str:
    size = 0
    chars: List[str] = []
    for char in text:
        char_size = len(char.encode("utf-8"))
        if chars and size + char_size > max_bytes:
            break
        chars.append(char)
        size += char_size
    return "".join(chars)


def split_long_sentence(sentence: str, max_bytes: int) -> List[str]:
    sentence = sentence.strip()
    if not sentence:
        return []
    if _utf8_len(sentence) <= max_bytes:
        return [sentence]

    parts: List[str] = []
    remaining = sentence
    while _utf8_len(remaining) > max_bytes:
        window = _window_within_bytes(remaining, max_bytes)
        split_pos = -1
        for match in SPLIT_HINT_PATTERN.finditer(window):
            if match.start() > 0:
                split_pos = match.start()
        if split_pos <= 0:
            split_pos = len(window)

        piece = remaining[:split_pos].strip()
        if not piece:
            piece = window.strip()
            split_pos = len(window)
        parts.append(piece)
        remaining = remaining[split_pos:].strip()

    if remaining:
        parts.append(remaining)
    return parts


def split_text(text: str, max_bytes: int) -> List[str]:
    sentences: List[str] = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        for part in SENTENCE_SPLIT_PATTERN.split(line):
            part = part.strip()
            if part:
                sentences.extend(split_long_sentence(part, max_bytes))

    chunks: List[str] = []
    current = ""
    for sentence in sentences:
        if not current:
            current = sentence
        elif _utf8_len(current) + 1 + _utf8_len(sentence) <= max_bytes:
            current = f"{current} {sentence}"
        else:
            chunks.append(current)
            current = sentence
    if current:
        chunks.append(current)
    return chunks


def parse_pcm_content_type(content_type: str) -> tuple[int, int]:
    rate_match = PCM_RATE_PATTERN.search(content_type or "")
    channel_match = PCM_CHANNELS_PATTERN.search(content_type or "")
    rate = int(rate_match.group(1)) if rate_match else DEFAULT_PCM_RATE
    channels = int(channel_match.group(1)) if channel_match else DEFAULT_PCM_CHANNELS
    if rate <= 0 or channels <= 0:
        raise RuntimeError(f"Invalid PCM content type: {content_type!r}")
    return rate, channels


def normalize_pcm(pcm: bytes, channels: int) -> bytes:
    frame_bytes = 2 * channels
    usable = len(pcm) - (len(pcm) % frame_bytes)
    pcm = pcm[:usable]
    if channels == 1:
        return pcm
    if channels != 2:
        raise RuntimeError(f"Unsupported PCM channel count: {channels}")

    samples = array.array("h")
    samples.frombytes(pcm)
    if sys.byteorder != "little":
        samples.byteswap()
    mixed = array.array(
        "h",
        ((samples[index] + samples[index + 1]) // 2 for index in range(0, len(samples), 2)),
    )
    if sys.byteorder != "little":
        mixed.byteswap()
    return mixed.tobytes()


def apply_edge_fade(pcm: bytes, sample_rate: int, fade_ms: int = EDGE_FADE_MS) -> bytes:
    if len(pcm) < 4 or fade_ms <= 0:
        return pcm
    samples = array.array("h")
    samples.frombytes(pcm)
    if sys.byteorder != "little":
        samples.byteswap()
    fade = min(len(samples) // 2, max(1, int(sample_rate * fade_ms / 1000)))
    if fade <= 1:
        return pcm
    for index in range(fade):
        in_gain = index / fade
        out_gain = 1.0 - in_gain
        samples[index] = int(samples[index] * in_gain)
        samples[-1 - index] = int(samples[-1 - index] * out_gain)
    if sys.byteorder != "little":
        samples.byteswap()
    return samples.tobytes()


def silence_pcm(duration_ms: int, sample_rate: int) -> bytes:
    if duration_ms <= 0:
        return b""
    sample_count = max(1, int(sample_rate * duration_ms / 1000))
    return b"\x00\x00" * sample_count


def pcm_to_wav(pcm: bytes, sample_rate: int) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm)
    return buffer.getvalue()


def _openrouter_error_message(status: int, body: bytes) -> str:
    text = body.decode("utf-8", "replace").strip()
    try:
        payload = json.loads(text) if text else None
    except json.JSONDecodeError:
        payload = None
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict) and error.get("message"):
            return f"OpenRouter error {status}: {error['message']}"
        if isinstance(error, str) and error.strip():
            return f"OpenRouter error {status}: {error.strip()}"
        if isinstance(payload.get("message"), str) and payload["message"].strip():
            return f"OpenRouter error {status}: {payload['message'].strip()}"
    if text:
        return f"OpenRouter error {status}: {text[:300]}"
    return f"OpenRouter error {status}."


def synthesize_pcm(text: str, voice_id: str) -> tuple[bytes, int]:
    api_key = openrouter_api_key()
    if not api_key:
        raise RuntimeError(
            "Set OPENROUTER_API_KEY in the environment or in .env."
        )

    payload = {
        "model": DRAMA3_MODEL,
        "input": text,
        "voice": voice_id,
        "response_format": "pcm",
        "provider": {"options": {"fish-audio": {"latency": "normal"}}},
    }
    request = urllib.request.Request(
        OPENROUTER_SPEECH_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://apertso.github.io/tts-mini-studio",
            "X-Title": "TTS Mini Studio",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            content_type = response.headers.get("Content-Type", "")
            audio = response.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(_openrouter_error_message(exc.code, exc.read())) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenRouter request failed: {exc.reason}") from exc

    if "mpeg" in content_type.lower():
        raise RuntimeError("OpenRouter returned MP3 instead of PCM.")
    if not audio:
        raise RuntimeError("OpenRouter returned empty audio.")

    rate, channels = parse_pcm_content_type(content_type)
    print(f"OpenRouter PCM content-type={content_type or '<missing>'} rate={rate} channels={channels}")
    return normalize_pcm(audio, channels), rate


def _fish_speech_request(path: str, payload: dict | None = None) -> bytes:
    base_url = fish_speech_base_url()
    if not base_url:
        raise RuntimeError("Set FISH_SPEECH_BASE_URL in the environment or in .env.")
    try:
        parsed = urlsplit(base_url)
    except ValueError as exc:
        raise RuntimeError("FISH_SPEECH_BASE_URL must be an HTTP(S) base URL.") from exc
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or "?" in base_url
        or "#" in base_url
    ):
        raise RuntimeError("FISH_SPEECH_BASE_URL must be an HTTP(S) base URL.")

    headers = {"Accept": "application/json" if payload is None else "audio/wav"}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    api_key = fish_speech_api_key()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    request = urllib.request.Request(f"{base_url}{path}", data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Fish Speech {path} returned HTTP {exc.code}.") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Fish Speech {path} request failed: {exc}") from exc


def _check_fish_speech_voice(voice_id: str) -> None:
    response = _fish_speech_request("/v1/references/list")
    try:
        references = json.loads(response)["reference_ids"]
        if not isinstance(references, list):
            raise TypeError("expected a list of references")
    except (ValueError, KeyError, TypeError) as exc:
        raise RuntimeError("Fish Speech returned an invalid voice reference list.") from exc
    if voice_id not in references:
        raise RuntimeError(f"Fish Speech voice reference {voice_id!r} is not registered.")


def _synthesize_fish_speech_pcm(text: str, voice_id: str) -> tuple[bytes, int]:
    payload = {
        "text": text,
        "format": "wav",
        "streaming": False,
    }
    if voice_id != "surprise":
        payload["reference_id"] = voice_id
    audio = _fish_speech_request("/v1/tts", payload)
    try:
        with wave.open(io.BytesIO(audio), "rb") as wav_file:
            channels = wav_file.getnchannels()
            rate = wav_file.getframerate()
            frame_count = wav_file.getnframes()
            if wav_file.getsampwidth() != 2 or channels not in (1, 2) or rate <= 0:
                raise wave.Error("expected mono or stereo 16-bit PCM")
            pcm = wav_file.readframes(frame_count)
            if not pcm or len(pcm) != frame_count * channels * 2:
                raise wave.Error("empty or incomplete audio")
    except (wave.Error, EOFError) as exc:
        raise RuntimeError(f"Fish Speech returned invalid WAV audio: {exc or 'missing WAV header'}.") from exc
    return normalize_pcm(pcm, channels), rate


def generate_audio_chunks(
    text_chunks: List[str],
    voice_selection: dict,
    synthesize: Callable[[str, str], tuple[bytes, int]],
    progress_callback: Optional[ProgressCallback] = None,
    cancel_event: threading.Event | None = None,
) -> Iterator[tuple[bytes, int]]:
    total_chunks = len(text_chunks)
    print(f"Using Drama 3 voice: {voice_selection['id']} ({voice_selection['name']})")

    for index, chunk in enumerate(text_chunks):
        if cancel_event is not None and cancel_event.is_set():
            raise GenerationCancelledError("Generation was cancelled.")

        print(f"Generating chunk {index + 1}/{total_chunks}")
        # shortcut: a request already sent to the speech provider runs until it returns.
        pcm, sample_rate = synthesize(chunk, voice_selection["voice_id"])
        if progress_callback is not None:
            progress_callback(index + 1, total_chunks)
        if pcm:
            yield pcm, sample_rate


def generate_tts(
    text: str,
    voice_id: Optional[str] = None,
    language: str = "en",
    progress_callback: Optional[ProgressCallback] = None,
    cancel_event: threading.Event | None = None,
) -> bytes:
    text = (text or "").strip()
    if not text:
        raise ValueError("No text provided")
    if len(text) > MAX_TEXT_CHARACTERS:
        raise ValueError(
            f"Text exceeds maximum length: {MAX_TEXT_CHARACTERS} symbols "
            f"(got {len(text)})."
        )

    text_language = classify_text_language(text)
    requested_language = normalize_language_code(language)
    resolved_language = text_language if text_language in {"en", "ru"} else requested_language
    provider = speech_provider()
    if cancel_event is not None and cancel_event.is_set():
        raise GenerationCancelledError("Generation was cancelled.")
    voice_selection = resolve_voice(voice_id)
    byte_limit = MAX_REQUEST_UTF8_BYTES
    synthesize = synthesize_pcm
    if provider == "fish-speech":
        if voice_selection["voice_id"] != "surprise":
            _check_fish_speech_voice(voice_selection["voice_id"])
        byte_limit = FISH_SPEECH_MAX_REQUEST_UTF8_BYTES
        synthesize = _synthesize_fish_speech_pcm
    elif voice_selection["voice_id"] == "surprise":
        raise ValueError("The Surprise voice requires the Fish Speech provider.")

    text_chunks = split_text(text, max_bytes=byte_limit)
    if not text_chunks:
        raise ValueError("No valid text provided")

    print(
        f"Total chunks: {len(text_chunks)}, byte_limit={byte_limit}, "
        f"language={resolved_language}, provider={provider}"
    )

    pieces: List[bytes] = []
    sample_rate: Optional[int] = None
    for index, (pcm, chunk_rate) in enumerate(
        generate_audio_chunks(
            text_chunks=text_chunks,
            voice_selection=voice_selection,
            synthesize=synthesize,
            progress_callback=progress_callback,
            cancel_event=cancel_event,
        )
    ):
        if sample_rate is None:
            sample_rate = chunk_rate
        elif chunk_rate != sample_rate:
            raise RuntimeError(
                f"Speech provider changed PCM rate from {sample_rate} to {chunk_rate}."
            )
        faded = apply_edge_fade(pcm, sample_rate)
        if index > 0:
            pieces.append(silence_pcm(INTER_CHUNK_PAUSE_MS, sample_rate))
        pieces.append(faded)

    if sample_rate is None or not pieces:
        raise RuntimeError("Generation failed: no audio chunks were produced")
    return pcm_to_wav(b"".join(pieces), sample_rate)
