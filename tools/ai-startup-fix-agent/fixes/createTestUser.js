// tools/ai-startup-fix-agent/fixes/createTestUser.js

import fs from "fs";

/**
 * Erzeugt einen YAML-Patch, der in die GitHub Workflow-Datei eingefügt wird.
 * Dieser Patch erstellt automatisch einen Django-Test-User in der CI-Datenbank.
 */
export function generateCreateUserPatch() {
    return `
- name: Create test user
  working-directory: django
  env:
    DJANGO_SETTINGS_MODULE: praxi_backend.settings.dev
    SYS_DB_NAME: praxi
    SYS_DB_USER: praxi
    SYS_DB_PASSWORD: praxi
    SYS_DB_HOST: 127.0.0.1
    SYS_DB_PORT: 5432
  run: |
    echo "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='test').exists():
    User.objects.create_user('test', password='test123')
" | python manage.py shell
`;
}

/**
 * Fügt den Patch ans Ende einer Workflow-Datei an, falls er noch nicht existiert.
 */
export function applyCreateUserPatch(workflowPath) {
    const patch = generateCreateUserPatch();
    const content = fs.readFileSync(workflowPath, "utf8");

    if (content.includes("Create test user")) {
        console.log("⚠️  Patch bereits vorhanden – wird nicht erneut hinzugefügt.");
        return false;
    }

    fs.writeFileSync(workflowPath, content + "\n" + patch);
    console.log("✅ Test-User-Patch erfolgreich hinzugefügt.");
    return true;
}
