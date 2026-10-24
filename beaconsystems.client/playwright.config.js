import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
    testDir: "./tests/e2e",
    outputDir: "./test-results",
    reporter: [["list"], ["html", { outputFolder: "playwright-report", open: "never" }]],
    workers: 1,
    use: {
        baseURL: "https://127.0.0.1:4173",
        ignoreHTTPSErrors: true,
        trace: "retain-on-failure",
        screenshot: "only-on-failure",
    },
    webServer: {
        command: "npm run dev -- --host 127.0.0.1 --port 4173",
        url: "https://127.0.0.1:4173",
        ignoreHTTPSErrors: true,
        reuseExistingServer: true,
        env: {
            VITE_API_BASE_URL: "https://api.beacon.test",
        },
    },
    projects: [
        { name: "chromium-laptop", use: { ...devices["Desktop Chrome"], viewport: { width: 1366, height: 768 } } },
        { name: "firefox-desktop", use: { ...devices["Desktop Firefox"], viewport: { width: 1920, height: 1080 } } },
        { name: "webkit-desktop", use: { ...devices["Desktop Safari"] } },
        { name: "chromium-phone", use: { ...devices["Galaxy S9+"] } },
        { name: "chromium-tablet", use: { ...devices["iPad (gen 7)"] } },
    ],
});
