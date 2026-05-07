import { html } from "../lib/html.js";
import { clampPercent } from "../utils/audioUtils.js";
import { DownloadIcon, PauseIcon, PlayIcon } from "./icons.js";

export const PlayerPanel = ({
    playerVisible,
    isPlaying,
    loadedPercent,
    playedPercent,
    timeDisplay,
    onTogglePlayback,
    onSeek,
    onDownload,
    canDownload,
    isDownloading,
    playerStateClass,
    playerStateLabel,
    playerDescription,
}) => {
    if (!playerVisible) {
        return null;
    }

    const safeLoaded = clampPercent(loadedPercent);
    const safePlayed = clampPercent(playedPercent);
    const loadedScale = safeLoaded / 100;
    const playedScale = safePlayed / 100;
    const timeParts = String(timeDisplay).split(" / ");
    const currentTime = timeParts[0] || "0:00";
    const totalTime = timeParts[1] || "0:00";

    return html`
        <section className="player-panel">
            <div className="player-transport" role="group" aria-label=${playerDescription}>
                <button
                    className="play-btn"
                    type="button"
                    onClick=${onTogglePlayback}
                    disabled=${safeLoaded === 0}
                    aria-label=${isPlaying ? "Pause" : "Play"}
                >
                    ${isPlaying ? PauseIcon() : PlayIcon()}
                </button>

                <div className="track-shell">
                    <span className="track-time track-time-current">${currentTime}</span>
                    <div className="track">
                        <div className="track-rail"></div>
                        <div className="track-loaded" style=${{ "--track-scale": loadedScale }}></div>
                        <div className="track-played" style=${{ "--track-scale": playedScale }}></div>
                        <input
                            className="range-input"
                            type="range"
                            min="0"
                            max="100"
                            step="0.01"
                            value=${safePlayed}
                            onInput=${onSeek}
                            onChange=${onSeek}
                            disabled=${safeLoaded === 0}
                            aria-label="Audio position"
                        />
                    </div>
                    <span className="track-time track-time-total">${totalTime}</span>
                </div>

                <button
                    className="download-btn"
                    type="button"
                    onClick=${onDownload}
                    disabled=${!canDownload}
                    aria-label=${isDownloading ? "Downloading WAV" : "Download WAV"}
                    title=${isDownloading ? "Downloading WAV" : "Download WAV"}
                >
                    ${DownloadIcon()}
                </button>
            </div>
        </section>
    `;
};
