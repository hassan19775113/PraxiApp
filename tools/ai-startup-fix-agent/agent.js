// tools/ai-startup-fix-agent/agent.js

import { detectIssue } from "./logParser.js";
import { getFixStrategy } from "./strategy.js";
import { applyPatch } from "./patcher.js";
import { commitAndPush } from "./git.js";

// Fix-Module
import { generateCreateUserPatch } from "./fixes/createTestUser.js";
import { applyFixAuthSetup } from "./fixes/fixAuthSetup.js";
import { applyFixDbEnvVariables } from "./fixes/fixDbEnvVariables.js";
import { applyFixDjangoSettings } from "./fixes/fixDjangoSettings.js";

/**
 * @param {string} log
 * @param {string} workflowPath
 * @param {{dryRun?: boolean, noPush?: boolean, verbose?: boolean}} options
 */
export async function runStartupFixAgent(log, workflowPath, options = {}) {
    const { dryRun = false, noPush = false, verbose = false } = options;

    console.log("🚀 Starte AI Startup Fix Agent...");
    if (verbose) {
        console.log("🔧 Optionen:", options);
    }

    console.log("🔍 Analysiere Log...");
    const issue = detectIssue(log);
    console.log(`➡️  Erkanntes Problem: ${issue}`);

    const strategy = getFixStrategy(issue);
    console.log(`➡️  Strategie: ${strategy.type} – ${strategy.description}`);

    let patchApplied = false;

    // 3. Fix ausführen
    switch (strategy.type) {
        case "CREATE_TEST_USER": {
            console.log("🛠  Erzeuge Patch für Test-User...");
            const patch = generateCreateUserPatch();

            if (dryRun) {
                console.log("🟨 Dry-Run aktiv – Patch wird NICHT geschrieben.");
                patchApplied = true;
            } else {
                patchApplied = applyPatch(workflowPath, patch);
            }
            break;
        }

        case "FIX_AUTH_SETUP": {
            console.log("🛠  Repariere auth.setup.ts...");
            const authSetupPath = "tests/auth.setup.ts";

            if (dryRun) {
                console.log(`🟨 Dry-Run aktiv – Datei würde repariert: ${authSetupPath}`);
                patchApplied = true;
            } else {
                patchApplied = applyFixAuthSetup(authSetupPath);
            }
            break;
        }

        case "FIX_DB_ENV_VARIABLES": {
            console.log("🛠  Korrigiere DB-ENV-Variablen im Workflow...");
            if (dryRun) {
                console.log(`🟨 Dry-Run aktiv – ENV-Patch würde in ${workflowPath} eingefügt.`);
                patchApplied = true;
            } else {
                patchApplied = applyFixDbEnvVariables(workflowPath);
            }
            break;
        }

        case "FIX_DJANGO_SETTINGS_MODULE": {
            console.log("🛠  Repariere Django Settings im Workflow...");
            if (dryRun) {
                console.log(`🟨 Dry-Run aktiv – Django-Settings-Patch würde in ${workflowPath} eingefügt.`);
                patchApplied = true;
            } else {
                patchApplied = applyFixDjangoSettings(workflowPath);
            }
            break;
        }

        default:
            console.log("⚠️  Kein implementiertes Fix-Modul für diese Strategie.");
            return {
                issue,
                strategy: strategy.type,
                patchApplied: false,
                committed: false,
                pushed: false
            };
    }

    if (!patchApplied) {
        console.log("⚠️  Patch wurde nicht angewendet. Kein Commit.");
        return {
            issue,
            strategy: strategy.type,
            patchApplied: false,
            committed: false,
            pushed: false
        };
    }

    if (dryRun) {
        console.log("🟨 Dry-Run aktiv – kein Commit, kein Push.");
        return {
            issue,
            strategy: strategy.type,
            patchApplied: true,
            committed: false,
            pushed: false
        };
    }

    console.log("📦 Erstelle Commit & Push...");
    const commitSuccess = commitAndPush(
        `AI Startup Fix Agent applied fix: ${strategy.type}`,
        { push: !noPush }
    );

    return {
        issue,
        strategy: strategy.type,
        patchApplied: true,
        committed: commitSuccess,
        pushed: commitSuccess && !noPush
    };
}
