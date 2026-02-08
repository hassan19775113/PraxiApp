// tools/ai-startup-fix-agent/patcher.js

import fs from "fs";

/**
 * Prüft, ob eine Datei existiert.
 */
export function fileExists(path) {
    return fs.existsSync(path);
}

/**
 * Liest eine Datei als UTF-8.
 */
export function readFile(path) {
    return fs.readFileSync(path, "utf8");
}

/**
 * Schreibt eine Datei vollständig neu.
 */
export function writeFile(path, content) {
    fs.writeFileSync(path, content, "utf8");
}

/**
 * Fügt einen Patch ans Ende einer Datei an,
 * aber nur, wenn der Patch noch nicht existiert.
 */
export function applyPatch(filePath, patchContent) {
    if (!fileExists(filePath)) {
        console.error(`❌ Datei nicht gefunden: ${filePath}`);
        return false;
    }

    const original = readFile(filePath);

    // Patch bereits vorhanden?
    if (original.includes(patchContent.trim())) {
        console.log("⚠️  Patch bereits vorhanden – wird übersprungen.");
        return false;
    }

    const updated = original + "\n" + patchContent;

    writeFile(filePath, updated);

    console.log(`✅ Patch erfolgreich angewendet auf: ${filePath}`);
    return true;
}

/**
 * Fügt einen Patch an einer bestimmten Stelle ein (optional).
 * Beispiel: vor einem bestimmten YAML-Step.
 */
export function insertPatchBefore(filePath, marker, patchContent) {
    if (!fileExists(filePath)) {
        console.error(`❌ Datei nicht gefunden: ${filePath}`);
        return false;
    }

    const original = readFile(filePath);

    if (original.includes(patchContent.trim())) {
        console.log("⚠️  Patch bereits vorhanden – wird übersprungen.");
        return false;
    }

    if (!original.includes(marker)) {
        console.error(`⚠️  Marker nicht gefunden: ${marker}`);
        return false;
    }

    const updated = original.replace(marker, patchContent + "\n" + marker);

    writeFile(filePath, updated);

    console.log(`✅ Patch erfolgreich vor Marker eingefügt: ${marker}`);
    return true;
}
