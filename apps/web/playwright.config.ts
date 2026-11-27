import { defineConfig } from "@playwright/test";

const PORT = 4311;

export default defineConfig({
  testDir: "e2e",
  testMatch: "**/*.e2e.ts",
  use: { baseURL: `http://127.0.0.1:${PORT}` },
  webServer: {
    command: `node scripts/serve-export.mjs out ${PORT}`,
    port: PORT,
    reuseExistingServer: true,
  },
});
