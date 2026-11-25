# Voice reference sources

Each folder in `voice_references/` is a Fish Speech reference: `sample.wav` plus its `sample.lab` transcript. The Drama 3 image copies them to `/app/references/<id>`. The voice IDs match `SELF_HOSTED_VOICES` in [`tts/voices.py`](../tts/voices.py).

The English voices and Mikhail (`ru-male-2`) are LibriVox audiobook readings. Their names (Emma, Oliver, Mikhail and so on) are invented. They are not the readers' names: the dataset terms ask users not to identify the readers.

Masha, Sveta and Dima (`ru-female-1`, `ru-female-2`, `ru-male-1`) are professional actors from the Dialogs studio corpus. They keep the names the dataset gives them. The actors gave written consent for open release and lawful use, including commercial use.

The web UI plays `docs/voice-previews/<id>.mp3` as a preview of each voice. Each preview is the same clip re-encoded to mono 64 kbps MP3:

```powershell
ffmpeg -i assets/voice_references/<id>/sample.wav -ac 1 -codec:a libmp3lame -b:a 64k docs/voice-previews/<id>.mp3
```

| Voice ID | Dataset | Clip |
| --- | --- | --- |
| `en-female-1` | LibriTTS-R, test.clean, speaker 1580 | row 4511 |
| `en-female-2` | LibriTTS-R, test.clean, speaker 237 | row 1550 |
| `en-male-1` | LibriTTS-R, test.clean, speaker 8230 | row 1826 |
| `en-male-2` | LibriTTS-R, test.clean, speaker 7021 | row 3615 |
| `ru-female-1` | Dialogs, speaker M (Masha), neutral | `wavs/masha_dima_part12_312.wav` |
| `ru-female-2` | Dialogs, speaker S (Sveta), neutral | `wavs/masha_sveta_part8_206.wav` |
| `ru-male-1` | Dialogs, speaker D (Dima), neutral | `wavs/masha_dima_part3_206.wav` |
| `ru-male-2` | Russian LibriSpeech, test, speaker 4372 | row 1049 |

## Licenses and attribution

- **LibriTTS-R** by Koizumi et al. (2023), derived from LibriTTS and LibriSpeech. Licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Copy used: [mythicinfinity/libritts_r](https://huggingface.co/datasets/mythicinfinity/libritts_r). The reference clips are unmodified apart from the WAV container. The web previews are also re-encoded to MP3.
- **Dialogs** by I. Shigabeev and I. Latyshev (Langswap), Interspeech 2026 ([paper](https://arxiv.org/abs/2607.14310)). Licensed under OpenRAIL, which allows commercial use and redistribution. Copy used: [langswap/dialogs-ru-emotional-conversations](https://huggingface.co/datasets/langswap/dialogs-ru-emotional-conversations). The reference clips are unmodified; the web previews are re-encoded to MP3. The full license is in [`voice_references/LICENSE-DIALOGS.md`](voice_references/LICENSE-DIALOGS.md). Its Section 2 use restrictions apply to these clips, the voices and all audio generated with them, and anyone who receives them must follow those restrictions too.
- **Russian LibriSpeech (RuLS)**, [OpenSLR 96](https://openslr.org/96). Public domain in the USA. Copy used: [istupakov/russian_librispeech](https://huggingface.co/datasets/istupakov/russian_librispeech).
