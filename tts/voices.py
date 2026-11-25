from __future__ import annotations

from typing import Dict


# Fish Official library voices. Drama 3 reads English and Russian in these voices.
FISH_VOICES = [
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

VOICE_MAP: Dict[str, dict] = {voice["id"]: voice for voice in FISH_VOICES}
VOICE_MAP["surprise"] = {"id": "surprise", "name": "Surprise", "locale": "en-US"}
DEFAULT_VOICE_ID = FISH_VOICES[0]["id"]


def list_available_voices() -> list:
    return [
        {
            "id": voice["id"],
            "name": voice["name"],
            "gender": voice["gender"],
            "source_type": "preset",
            "locale": voice["locale"],
        }
        for voice in FISH_VOICES
    ]


def resolve_voice(voice_id: str | None = None) -> dict:
    normalized = str(voice_id or "").strip() or DEFAULT_VOICE_ID
    voice = VOICE_MAP.get(normalized)
    if voice is None:
        raise ValueError(f"Unknown voice_id: {normalized}")

    return {
        "id": voice["id"],
        "name": voice["name"],
        "source_type": "preset",
        "voice_id": voice["id"],
        "locale": voice["locale"],
    }
