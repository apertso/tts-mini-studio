import { html } from "../lib/html.js";

export const PlayIcon = () => html`
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="M7 5.25a1 1 0 0 1 1.52-.86l9.5 6.25a1 1 0 0 1 0 1.72l-9.5 6.25A1 1 0 0 1 7 17.5z"></path>
    </svg>
`;

export const PauseIcon = () => html`
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="M7.5 5h3a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1h-3a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1zm6 0h3a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1h-3a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1z"></path>
    </svg>
`;

export const DownloadIcon = () => html`
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="M11 4a1 1 0 1 1 2 0v8.59l2.3-2.29a1 1 0 1 1 1.4 1.41l-4 4a1 1 0 0 1-1.4 0l-4-4a1 1 0 0 1 1.4-1.41L11 12.59z"></path>
        <path d="M5 18a1 1 0 0 1 1-1h12a1 1 0 1 1 0 2H6a1 1 0 0 1-1-1z"></path>
    </svg>
`;

export const SpeakIcon = () => html`
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="M11 5a1 1 0 0 1 2 0v2.5a1 1 0 1 1-2 0z"></path>
        <path d="M11 16.5a1 1 0 1 1 2 0V19a1 1 0 1 1-2 0z"></path>
        <path d="M5 11a1 1 0 0 1 0 2H2.5a1 1 0 1 1 0-2z"></path>
        <path d="M21.5 11a1 1 0 1 1 0 2H19a1 1 0 1 1 0-2z"></path>
        <path d="M7.05 7.05a1 1 0 0 1 1.42 0l1.06 1.06a1 1 0 1 1-1.42 1.42L7.05 8.47a1 1 0 0 1 0-1.42z"></path>
        <path d="M14.47 14.47a1 1 0 0 1 1.42 0l1.06 1.06a1 1 0 0 1-1.42 1.42l-1.06-1.06a1 1 0 0 1 0-1.42z"></path>
        <path d="M16.95 7.05a1 1 0 0 1 0 1.42l-1.06 1.06a1 1 0 0 1-1.42-1.42l1.06-1.06a1 1 0 0 1 1.42 0z"></path>
        <path d="M9.53 14.47a1 1 0 0 1 0 1.42l-1.06 1.06a1 1 0 0 1-1.42-1.42l1.06-1.06a1 1 0 0 1 1.42 0z"></path>
    </svg>
`;

export const VoiceIcon = () => html`
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <rect x="5" y="9" width="2" height="6" rx="1" />
        <rect x="9" y="5" width="2" height="14" rx="1" />
        <rect x="13" y="8" width="2" height="8" rx="1" />
        <rect x="17" y="10" width="2" height="4" rx="1" />
    </svg>
`;
