import { defineConfig, devices } from '@playwright/test';

const artifactsOff = process.env.PW_ARTIFACTS === '0';

export default defineConfig({
  // Alle Tests liegen jetzt unter tests/
  testDir: './tests',

  timeout: 90_000,
  expect: { timeout: 10_000 },

  reporter: [['list'], ['html']],

  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:8000',
    headless: true,

    trace: artifactsOff ? 'off' : 'retain-on-failure',
    video: artifactsOff ? 'off' : 'retain-on-failure',
    screenshot: artifactsOff ? 'off' : 'only-on-failure',

    // Resolve via repo root relative path for CI stability
    storageState: 'tests/fixtures/storageState.json',
  },

  // Pfad korrigiert
  globalSetup: './tests/fixtures/auth.setup.ts',

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});