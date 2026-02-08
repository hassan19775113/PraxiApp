// tools/ai-startup-fix-agent/git.js

import { execSync } from "child_process";

function run(cmd) {
    try {
        console.log(`🟦 git> ${cmd}`);
        const output = execSync(cmd, { encoding: "utf8" });
        return output.trim();
    } catch (err) {
        console.error(`❌ Git-Fehler bei: ${cmd}`);
        console.error(err.message);
        return null;
    }
}

export function gitAdd(path = ".") {
    return run(`git add ${path}`);
}

export function gitCommit(message) {
    return run(`git commit -m "${message}"`);
}

export function gitPush() {
    return run("git push");
}

/**
 * Add → Commit → optional Push
 * options.push = false → nur Commit, kein Push
 */
export function commitAndPush(message, options = { push: true }) {
    console.log("📦 Erstelle Commit...");

    const add = gitAdd(".");
    if (add === null) {
        console.log("⚠️  git add fehlgeschlagen.");
        return false;
    }

    const commit = gitCommit(message);
    if (commit === null) {
        console.log("⚠️  Nichts zu committen oder Fehler beim Commit.");
        return false;
    }

    if (!options.push) {
        console.log("🟨 Push deaktiviert – Commit wurde erstellt.");
        return true;
    }

    const push = gitPush();
    if (push === null) {
        console.log("⚠️  Commit erstellt, aber Push fehlgeschlagen.");
        return false;
    }

    console.log("🚀 Änderungen erfolgreich gepusht.");
    return true;
}
