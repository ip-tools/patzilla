const { defineConfig, devices } = require('@playwright/test');

const baseURL = 'http://127.0.0.1:5543';

module.exports = defineConfig({
  testDir: './tests/ui',

  use: {
    baseURL,
    trace: 'retain-on-failure',
  },

  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],

  webServer: {
    command: '.venv/bin/patzilla serve tests/ui/ci.ini',
    url: `${baseURL}/navigator/`,
    timeout: 60_000,
    reuseExistingServer: true,
    stdout: 'pipe',
    stderr: 'pipe',
  },
});
