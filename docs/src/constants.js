const runtimeConfig = (typeof window !== "undefined" && window.__TTS_CONFIG__)
    ? window.__TTS_CONFIG__
    : {};

const getStringSetting = (value, fallback = "") => {
    if (typeof value !== "string") return fallback;
    const normalized = value.trim();
    return normalized || fallback;
};

const getNumericSetting = (value, fallback, min) => {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return fallback;
    return Math.max(min, Math.floor(numeric));
};

export const API_MODE = getStringSetting(runtimeConfig.apiMode, "runpod").toLowerCase();
export const API_BASE_URL = getStringSetting(runtimeConfig.apiBaseUrl, "http://localhost:5000");
export const RUNPOD_PROXY_URL = getStringSetting(runtimeConfig.runpodProxyUrl, "https://twilight-dream-8480.djlokiart.workers.dev/api/runpod");
export const RUNPOD_POLL_INTERVAL_MS = getNumericSetting(runtimeConfig.runpodPollIntervalMs, 2000, 500);
export const RUNPOD_TIMEOUT_MS = getNumericSetting(runtimeConfig.runpodTimeoutMs, 900000, 10000);
export const MAX_TEXT_CHARACTERS = getNumericSetting(runtimeConfig.maxTextCharacters, 50000, 1);
export const DEFAULT_LANGUAGE = "en";
// Mirrors SELF_HOSTED_VOICES in tts/voices.py; the Drama 3 image bundles a reference for each.
export const RUNPOD_FALLBACK_VOICES = [
    { id: "en-female-1", name: "Female 1", source_type: "preset", locale: "en-US" },
    { id: "en-female-2", name: "Female 2", source_type: "preset", locale: "en-US" },
    { id: "en-male-1", name: "Male 1", source_type: "preset", locale: "en-US" },
    { id: "en-male-2", name: "Male 2", source_type: "preset", locale: "en-US" },
    { id: "ru-female-1", name: "Female 1", source_type: "preset", locale: "ru-RU" },
    { id: "ru-female-2", name: "Female 2", source_type: "preset", locale: "ru-RU" },
    { id: "ru-male-1", name: "Male 1", source_type: "preset", locale: "ru-RU" },
    { id: "ru-male-2", name: "Male 2", source_type: "preset", locale: "ru-RU" },
    { id: "surprise", name: "Surprise", source_type: "preset", locale: "" },
];

export const STORAGE_KEYS = {
    text: "tts_text",
    voice: "tts_voice",
    pendingJob: "tts_pending_job_v1",
};
