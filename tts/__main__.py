from __future__ import annotations

from .config import (
    DRAMA3_MODEL,
    MODE,
    configure_stdio,
    speech_provider,
    speech_provider_configured,
    validate_mode,
)


def main() -> None:
    configure_stdio()
    mode = validate_mode(MODE)
    provider = speech_provider()
    print(f"Starting TTS backend in '{mode}' mode")
    print(f"Model={DRAMA3_MODEL}, provider={provider}, configured={speech_provider_configured(provider)}")

    if mode == "local":
        from .server import start_flask

        start_flask()
        return

    from .runpod import start_runpod

    start_runpod()


if __name__ == "__main__":
    main()
