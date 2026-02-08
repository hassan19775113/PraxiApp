// tools/ai-startup-fix-agent/strategy.js

/**
 * Mapping von Issue-Code → Fix-Strategie
 * Der AI Startup Fix Agent nutzt diese Strategien,
 * um zu entscheiden, welche Reparatur angewendet werden soll.
 */

export function getFixStrategy(issueCode) {
    switch (issueCode) {

        case "LOGIN_FAILED":
            return {
                type: "CREATE_TEST_USER",
                description: "Erzeuge einen Test-User in der Django-Datenbank und nutze ihn für E2E-Login."
            };

        case "STORAGE_STATE_MISSING":
            return {
                type: "FIX_AUTH_SETUP",
                description: "Repariere das auth.setup.ts, damit storageState.json korrekt erzeugt wird."
            };

        case "DB_PASSWORD_MISSING":
            return {
                type: "FIX_DB_ENV_VARIABLES",
                description: "Korrigiere die DB-Umgebungsvariablen im Workflow (SYS_DB_* statt DB_*)."
            };

        case "DB_CONNECTION_FAILED":
            return {
                type: "CHECK_DB_SERVICE_AND_ENV",
                description: "Prüfe PostgreSQL-Service und Verbindungsdaten (Host, Port, User, Passwort)."
            };

        case "DJANGO_SETTINGS_INVALID":
            return {
                type: "FIX_DJANGO_SETTINGS_MODULE",
                description: "Setze DJANGO_SETTINGS_MODULE korrekt und entferne veraltete Settings-Referenzen."
            };

        case "PLAYWRIGHT_API_CONTEXT_FAILED":
            return {
                type: "CHECK_API_CLIENT_CONFIG",
                description: "Prüfe api-client.ts und storageState-Pfad für Playwright request.newContext."
            };

        case "PLAYWRIGHT_TEST_FAILED":
            return {
                type: "ANALYZE_PLAYWRIGHT_TEST",
                description: "Analysiere fehlgeschlagene Tests und schlage gezielte Patches vor."
            };

        case "ENV_VARIABLE_MISSING":
            return {
                type: "CHECK_ENV_AND_SECRETS",
                description: "Prüfe GitHub Secrets, .env und Workflow-ENV auf fehlende Variablen."
            };

        case "MODULE_NOT_FOUND":
            return {
                type: "CHECK_DEPENDENCIES",
                description: "Prüfe package.json / requirements.txt und Installationsschritte im Workflow."
            };

        default:
            return {
                type: "NO_AUTOMATIC_FIX",
                description: "Kein bekannter automatischer Fix – manueller Review erforderlich."
            };
    }
}
