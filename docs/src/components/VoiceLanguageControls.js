import { React, html } from "../lib/html.js";

const { useState, useRef, useEffect } = React;

export const VoiceLanguageControls = ({
    voice,
    voices,
    voicesReady,
    voiceLoadFailed,
    onVoiceChange,
}) => {
    const [isOpen, setIsOpen] = useState(false);
    const containerRef = useRef(null);

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
                <span className="select-field-text">${selectedVoice.name}</span>
            </button>
            ${isOpen && voices.length > 0 ? html`
                <div className="custom-select-dropdown">
                    <div className="custom-select-scroll">
                        <div className="custom-select-group">Kokoro Voices</div>
                        ${voices.map((item) => html`
                            <button
                                key=${item.id}
                                type="button"
                                className=${`custom-select-option ${item.id === voice ? "selected" : ""}`}
                                onClick=${() => {
                                    onVoiceChange(item.id);
                                    setIsOpen(false);
                                }}
                            >
                                ${item.name}
                            </button>
                        `)}
                    </div>
                </div>
            ` : null}
        </div>
    `;
};
