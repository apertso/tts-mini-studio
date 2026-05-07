import { html } from "../lib/html.js";

export const TextInputPanel = ({
  text,
  charCount,
  maxTextCharacters,
  isTextTooLong,
  onTextChange,
  onSubmit,
  statusText,
  statusClass,
}) => {
  const safeCharCount = Math.max(0, Number(charCount) || 0);
  const safeMaxChars = Math.max(1, Number(maxTextCharacters) || 1);
  const overflowCount = Math.max(0, safeCharCount - safeMaxChars);

  const isVisible = Boolean(statusClass !== "status-idle" && statusText);
  const isError = statusClass === "status-error";

  const renderToastText = (txt) => {
    if (!txt) return null;
    if (txt.startsWith("Error: ")) {
      return html`<strong>Error</strong> ${txt.substring(7)}`;
    }
    if (txt.startsWith("Cancel failed: ")) {
      return html`<strong>Cancel failed</strong> ${txt.substring(14)}`;
    }
    return txt;
  };

  return html`
    <section className="input-panel">
      ${isVisible ? html`
        <div className=${`status-toast ${statusClass} is-visible`}>
          <span className="status-toast-icon" aria-hidden="true">
            ${isError ? html`
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
              </svg>
            ` : html`
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                <polyline points="22 4 12 14.01 9 11.01"></polyline>
              </svg>
            `}
          </span>
          <span className="status-toast-text">${renderToastText(statusText)}</span>
        </div>
      ` : null}
      <textarea
        id="tts-text"
        className="text-area"
        placeholder="Type or paste your text here..."
        aria-label="Text to synthesize"
        value=${text}
        aria-invalid=${isTextTooLong}
        onChange=${(event) => onTextChange(event.target.value)}
        onKeyDown=${(event) => {
          if (event.key === "Enter" && event.ctrlKey) {
            onSubmit();
          }
        }}
      ></textarea>
      ${isTextTooLong
        ? html`
            <p className="text-limit-warning">
              Text exceeds maximum length by ${overflowCount} symbols.
            </p>
          `
        : null}
    </section>
  `;
};
