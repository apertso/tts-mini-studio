import { html } from "../lib/html.js";
import { GenerateButton } from "./GenerateButton.js";
import { PlayerPanel } from "./PlayerPanel.js";
import { StudioHeader } from "./StudioHeader.js";
import { TextInputPanel } from "./TextInputPanel.js";
import { VoiceLanguageControls } from "./VoiceLanguageControls.js";
import { useTtsStudio } from "../state/useTtsStudio.js";

export const StudioPage = () => {
    const studio = useTtsStudio();

    return html`
        <div className="page-shell">
            <div className="motion-ribbons" aria-hidden="true"></div>
            ${StudioHeader()}
            <main className="studio-card">
                ${TextInputPanel({
                    text: studio.text,
                    charCount: studio.textCharCount,
                    maxTextCharacters: studio.maxTextCharacters,
                    isTextTooLong: studio.isTextTooLong,
                    onTextChange: studio.onTextChange,
                    onSubmit: studio.onPrimaryAction,
                    statusText: studio.actionStatusText,
                    statusClass: studio.actionStatusClass,
                })}

                <div className="control-dock">
                    <div className="control-dock-top">
                        ${PlayerPanel({
                            playerVisible: studio.playerVisible,
                            isPlaying: studio.isPlaying,
                            loadedPercent: studio.loadedPercent,
                            playedPercent: studio.playedPercent,
                            timeDisplay: studio.timeDisplay,
                            onTogglePlayback: studio.onTogglePlayback,
                            onSeek: studio.onSeek,
                            onDownload: studio.onDownload,
                            canDownload: studio.canDownload,
                            isDownloading: studio.isDownloading,
                            playerStateClass: studio.playerStateClass,
                            playerStateLabel: studio.playerStateLabel,
                            playerDescription: studio.playerDescription,
                        })}
                        <div className=${`char-count-display ${studio.isTextTooLong ? "error" : ""}`}>
                            ${studio.textCharCount}/${studio.maxTextCharacters}
                        </div>
                    </div>
                    <div className="control-dock-bottom">
                        ${VoiceLanguageControls({
                            voice: studio.voice,
                            voices: studio.voices,
                            voicesReady: studio.voicesReady,
                            voiceLoadFailed: studio.voiceLoadFailed,
                            onVoiceChange: studio.onVoiceChange,
                        })}

                        ${GenerateButton({
                            disabled: studio.isPrimaryActionDisabled,
                            isGenerating: studio.isGenerating,
                            label: studio.generationLabel,
                            progress: studio.streamProgress,
                            onClick: studio.onPrimaryAction,
                        })}
                    </div>
                </div>
            </main>
        </div>
    `;
};
