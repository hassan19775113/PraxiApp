// tools/ai-startup-fix-agent/index.js

import { detectIssue } from "./logParser.js";
import { getFixStrategy } from "./strategy.js";
import { applyPatch } from "./patcher.js";

// Fix-Module
import { generateCreateUserPatch } from "./fixes/createTestUser.js";

/**
 * Hauptfunktion des AI Startup Fix Agent.
 * Nimmt ein Log entgegen, erkennt das Problem und führt den passenden Fix aus.
 */
export async function runFixAgent(log, workflowPath) {
    console.log("🔍 Analysiere Log...");

    const issue = detectIssue(log);
    console.log(`➡️  Erkanntes Problem: ${issue}`);

    const strategy = getFixStrategy(issue);
    console.log(`➡️  Strategie: ${strategy.type}`);

    switch (strategy.type) {

        case "CREATE_TEST_USER": {
            console.log("🛠  Erzeuge Patch für Test-User...");
            const patch = generateCreateUserPatch();
            const result = applyPatch(workflowPath, patch);
            return {
                issue,
                strategy: strategy.type,
                success: result
            };
        }

        case "FIX_AUTH_SETUP":
        case "FIX_DB_ENV_VARIABLES":
        case "CHECK_DB_SERVICE_AND_ENV":
        case "FIX_DJANGO_SETTINGS_MODULE":
        case "CHECK_API_CLIENT_CONFIG":
        case "ANALYZE_PLAYWRIGHT_TEST":
        case "CHECK_ENV_AND_SECRETS":
        case "CHECK_DEPENDENCIES":
            console.log("⚠️  Fix-Modul für diese Strategie ist noch nicht implementiert.");
            return {
                issue,
                strategy: strategy.type,
                success: false
            };

        default:
            console.log("❓ Kein automatischer Fix verfügbar.");
            return {
                issue,
                strategy: "NO_AUTOMATIC_FIX",
                success: false
            };
    }
}

