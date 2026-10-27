import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e",
  workers: 1,
  webServer: process.env.CI && !process.env.FRONTEND_URL ? {
    command: "npm run preview -- --host 127.0.0.1 --port 5173",
    url: "http://127.0.0.1:5173",
    reuseExistingServer: false,
  } : undefined,
  timeout: 60_000,
  use: {
    baseURL: process.env.FRONTEND_URL || "http://127.0.0.1:5173",
    launchOptions: {
      executablePath:
        process.env.CHROME_PATH ||
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    },
    screenshot: "only-on-failure",
  },
});
