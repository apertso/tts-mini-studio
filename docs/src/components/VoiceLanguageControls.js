import { React, html } from "../lib/html.js";

const { useState, useRef, useEffect } = React;

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
                <span className="select-field-text">${voiceLabel(selectedVoice)}</span>
            </button>
            ${isOpen && voices.length > 0 ? html`
                <div className="custom-select-dropdown">
                    <div className="custom-select-scroll">
                        ${voiceGroups(voices).map((group) => html`
                            <div key=${group.label} className="custom-select-group">${group.label}</div>
                            ${group.items.map((item) => html`
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
                        `)}
                    </div>
                </div>
            ` : null}
        </div>
    `;
};
