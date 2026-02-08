// tools/ai-startup-fix-agent/logParser.js

/**
 * Root Cause Detection für den AI Fix Agent.
 * Erkennt typische Fehler aus:
 * - Playwright Logs
 * - Django Logs
 * - API Fehlern
 * - CI/CD Fehlern
 */

export function detectIssue(log) {
    const lower = log.toLowerCase();

    // 🔐 LOGIN FEHLER
    if (lower.includes("invalid credentials") ||
        lower.includes("login failed") ||
        lower.includes("non_field_errors") && lower.includes("credentials")) {
        return "LOGIN_FAILED";
    }

    // 🗄️ STORAGE STATE FEHLT
    if (lower.includes("storageState.json".toLowerCase()) &&
        lower.includes("no such file")) {
        return "STORAGE_STATE_MISSING";
    }

    // 🛢️ DB PASSWORT FEHLT
    if (lower.includes("fe_sendauth") ||
        lower.includes("password authentication failed") ||
        lower.includes("no password supplied")) {
        return "DB_PASSWORD_MISSING";
    }

    // 🛢️ DB VERBINDUNG FEHLGESCHLAGEN
    if (lower.includes("could not connect to server") ||
        lower.includes("connection refused") ||
        lower.includes("connection timed out")) {
        return "DB_CONNECTION_FAILED";
    }

    // ⚙️ DJANGO SETTINGS FEHLER
    if (lower.includes("django.core.exceptions.improperlyconfigured") ||
        lower.includes("settings module") && lower.includes("not found")) {
        return "DJANGO_SETTINGS_INVALID";
    }

    // 🧪 PLAYWRIGHT API FEHLER
    if (lower.includes("api request failed") ||
        lower.includes("request.newcontext") && lower.includes("error")) {
        return "PLAYWRIGHT_API_CONTEXT_FAILED";
    }

    // 🧪 PLAYWRIGHT TEST FEHLER
    if (lower.includes("test failed") ||
        lower.includes("expect") && lower.includes("received")) {
        return "PLAYWRIGHT_TEST_FAILED";
    }

    // 🧩 FEHLENDE ENV VARIABLEN
    if (lower.includes("environment variable") && lower.includes("not set")) {
        return "ENV_VARIABLE_MISSING";
    }

    // 📦 FEHLENDE MODULE
    if (lower.includes("cannot find module") ||
        lower.includes("module not found")) {
        return "MODULE_NOT_FOUND";
    }

    // ❓ UNBEKANNTER FEHLER
    return "UNKNOWN";
}
