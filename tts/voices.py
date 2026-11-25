from __future__ import annotations

from .config import speech_provider


# Fish Official library voices, available through OpenRouter. Drama 3 reads English and Russian in each.
CLOUD_VOICES = [
    {"id": "bf322df2096a46f18c579d0baa36f41d", "name": "Adrian", "gender": "male", "locale": "en-US"},
    {"id": "933563129e564b19a115bedd57b7406a", "name": "Sarah", "gender": "female", "locale": "en-US"},
    {"id": "536d3a5e000945adb7038665781a4aca", "name": "Ethan", "gender": "male", "locale": "en-US"},
    {"id": "b347db033a6549378b48d00acb0d06cd", "name": "Selene", "gender": "female", "locale": "en-US"},
    {"id": "fbc1029c018041d4b17f2c1e57222dff", "name": "Richard", "gender": "male", "locale": "en-GB"},
    {"id": "0efe38923c0b445ab09382e851ae1e30", "name": "Sophia", "gender": "female", "locale": "en-GB"},
    {"id": "b871e425b6c0442baa5cf73f6c336bbe", "name": "Artyom", "gender": "male", "locale": "ru-RU"},
    {"id": "bf75c2e80b0e441485eeec20330a75fa", "name": "Polina", "gender": "female", "locale": "ru-RU"},
    {"id": "2911dfe1c9d54419b24ed8c4a1489355", "name": "Dmitri", "gender": "male", "locale": "ru-RU"},
    {"id": "7adab54c80d34cba8c11463ab1502c9a", "name": "Maria", "gender": "female", "locale": "ru-RU"},
    {"id": "911cdc7841634850ba72d88f5ed8c576", "name": "Kira", "gender": "female", "locale": "ru-RU"},
    {"id": "de9a2c99fcee4dfbbaec90327eab36d8", "name": "Egor", "gender": "male", "locale": "ru-RU"},
]

# Self-hosted Fish Speech references from public audiobook datasets; see assets/VOICE_SOURCES.md.
# Names are invented, not the readers' own. Each ID is a folder with sample.wav and sample.lab, baked into the Drama 3 image as /app/references/<id>.
SELF_HOSTED_VOICES = [
    {"id": "en-female-1", "name": "Emma", "gender": "female", "locale": "en-US"},
    {"id": "en-female-2", "name": "Grace", "gender": "female", "locale": "en-US"},
    {"id": "en-male-1", "name": "Oliver", "gender": "male", "locale": "en-US"},
    {"id": "en-male-2", "name": "Henry", "gender": "male", "locale": "en-US"},
    {"id": "ru-female-1", "name": "Anna", "gender": "female", "locale": "ru-RU"},
    {"id": "ru-female-2", "name": "Vera", "gender": "female", "locale": "ru-RU"},
    {"id": "ru-male-1", "name": "Ivan", "gender": "male", "locale": "ru-RU"},
    {"id": "ru-male-2", "name": "Mikhail", "gender": "male", "locale": "ru-RU"},
    # Reference-free: Drama 3 picks a new voice on every request.
    {"id": "surprise", "name": "Surprise", "gender": "", "locale": ""},
]


def voice_catalog(provider: str | None = None) -> list:
    provider = provider or speech_provider()
    return SELF_HOSTED_VOICES if provider == "fish-speech" else CLOUD_VOICES


def default_voice_id(provider: str | None = None) -> str:
    return voice_catalog(provider)[0]["id"]


def list_available_voices(provider: str | None = None) -> list:
    return [{**voice, "source_type": "preset"} for voice in voice_catalog(provider)]


def resolve_voice(voice_id: str | None = None, provider: str | None = None) -> dict:
    catalog = voice_catalog(provider)
    normalized = str(voice_id or "").strip() or catalog[0]["id"]
    voice = next((item for item in catalog if item["id"] == normalized), None)
    if voice is None:
        raise ValueError(f"Unknown voice_id: {normalized}")

    return {
        "id": voice["id"],
        "name": voice["name"],
        "source_type": "preset",
        "voice_id": voice["id"],
        "locale": voice["locale"],
    }
