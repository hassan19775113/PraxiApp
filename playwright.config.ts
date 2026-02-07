import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  // Alle Tests liegen jetzt unter tests/
  testDir: './tests',

  timeout: 90_000,
  expect: { timeout: 10_000 },

  reporter: [['list'], ['html']],

  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:8000',
    headless: true,

    trace: 'retain-on-failure',
    video: 'retain-on-failure',
    screenshot: 'only-on-failure',

    // Pfad korrigiert
    storageState: './tests/fixtures/storageState.json',
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