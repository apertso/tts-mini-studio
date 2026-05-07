import { html } from "../lib/html.js";

export const StudioHeader = () => html`
    <header className="studio-header">
        <span className="brand-mark" aria-hidden="true">
            <span></span>
            <span></span>
            <span></span>
            <span></span>
            <span></span>
        </span>
        <h1 className="studio-title">TTS Mini Studio</h1>
    </header>
`;
