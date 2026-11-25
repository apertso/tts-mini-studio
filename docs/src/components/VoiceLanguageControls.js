import { React, html } from "../lib/html.js";
import { RUNPOD_FALLBACK_VOICES } from "../constants.js";
import { PauseIcon, PlayIcon } from "./icons.js";

const { useState, useRef, useEffect } = React;

// The local API lists the same self-hosted IDs without preview paths, so look them up by ID.
const previewUrl = (item) => item.preview || RUNPOD_FALLBACK_VOICES.find((v) => v.id === item.id)?.preview || "";

const groupLabel = (locale) => {
    const value = String(locale || "");
    if (value.startsWith("ru")) return "Russian";
    if (value.startsWith("en")) return "English";
    return "Random";
};

const voiceLabel = (item) => (item.locale ? `${groupLabel(item.locale)} · ${item.name}` : item.name);

const voiceGroups = (voices) => {
    const groups = [];
    for (const item of voices) {
        const label = groupLabel(item.locale);
        let group = groups.find((entry) => entry.label === label);
        if (!group) {
            group = { label, items: [] };
            groups.push(group);
        }
        group.items.push(item);
    }
    return groups;
};

export const VoiceLanguageControls = ({
    voice,
    voices,
    voicesReady,
    voiceLoadFailed,
    onVoiceChange,
}) => {
    const [isOpen, setIsOpen] = useState(false);
    const [previewingId, setPreviewingId] = useState("");
    const containerRef = useRef(null);
    const previewAudioRef = useRef(null);

    const stopPreview = () => {
        previewAudioRef.current?.pause();
        setPreviewingId("");
    };

    const togglePreview = (item) => {
        if (previewingId === item.id) {
            stopPreview();
            return;
        }
        if (!previewAudioRef.current) {
            previewAudioRef.current = new Audio();
            previewAudioRef.current.addEventListener("ended", () => setPreviewingId(""));
        }
        const audio = previewAudioRef.current;
        audio.src = previewUrl(item);
        setPreviewingId(item.id);
        audio.play().catch((error) => {
            console.error("Voice preview failed:", error);
            setPreviewingId("");
        });
    };

    useEffect(() => {
        if (!isOpen) stopPreview();
    }, [isOpen]);

    useEffect(() => () => previewAudioRef.current?.pause(), []);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (containerRef.current && !containerRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const selectedVoice = voices.find((v) => v.id === voice) || { name: voiceLoadFailed ? "Voices unavailable" : "Loading voices..." };

    return html`
        <div className="custom-select-container" ref=${containerRef} aria-label="Voice controls">
            <button
                type="button"
                className=${`select-shell ${isOpen ? "is-open" : ""}`}
                onClick=${() => voicesReady && setIsOpen(!isOpen)}
                disabled=${!voicesReady}
            >
                <span className="select-mark" aria-hidden="true">
                    <span></span>
                    <span></span>
                    <span></span>
                </span>
                <span className="select-field-text">${voiceLabel(selectedVoice)}</span>
            </button>
            ${isOpen && voices.length > 0 ? html`
                <div className="custom-select-dropdown">
                    <div className="custom-select-scroll">
                        ${voiceGroups(voices).map((group) => html`
                            <div key=${group.label} className="custom-select-group">${group.label}</div>
                            ${group.items.map((item) => html`
                                <div key=${item.id} className=${`custom-select-option ${item.id === voice ? "selected" : ""}`}>
                                    <button
                                        type="button"
                                        className="custom-select-option-label"
                                        onClick=${() => {
                                            onVoiceChange(item.id);
                                            setIsOpen(false);
                                        }}
                                    >
                                        ${item.name}
                                    </button>
                                    ${previewUrl(item) ? html`
                                        <button
                                            type="button"
                                            className=${`voice-preview-button ${previewingId === item.id ? "is-playing" : ""}`}
                                            aria-label=${`${previewingId === item.id ? "Stop" : "Listen to"} ${item.name}`}
                                            title=${previewingId === item.id ? "Stop preview" : "Listen"}
                                            onClick=${() => togglePreview(item)}
                                        >
                                            ${previewingId === item.id ? PauseIcon() : PlayIcon()}
                                        </button>
                                    ` : null}
                                </div>
                            `)}
                        `)}
                    </div>
                </div>
            ` : null}
        </div>
    `;
};
