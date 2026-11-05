import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

let currentRole = "platform_admin";
let identityRequests = 0;

async function setRole(page, role) {
    currentRole = role;
    await page.evaluate((nextRole) => sessionStorage.setItem("role", nextRole), role);
}

test.beforeEach(async ({ page }) => {
    currentRole = "platform_admin";
    identityRequests = 0;
    await page.addInitScript(() => {
        sessionStorage.setItem("token", "synthetic-role-test-token");
        if (!sessionStorage.getItem("role")) {
            sessionStorage.setItem("role", "platform_admin");
        }
        sessionStorage.setItem("username", "uat-role-user");
        sessionStorage.setItem("last_activity_at", String(Date.now()));
        sessionStorage.setItem("session_expires_at", new Date(Date.now() + 3_600_000).toISOString());
    });
    await page.route("https://api.beacon.test/dashboard/summary", (route) => route.fulfill({ json: {} }));
    await page.route("https://api.beacon.test/supervisor/queue", (route) => route.fulfill({ json: {} }));
    await page.route("https://api.beacon.test/cases/**", (route) => route.fulfill({ json: [] }));
    await page.route("https://api.beacon.test/sightings/**", (route) => route.fulfill({ json: [] }));
    await page.route("https://api.beacon.test/persons/registry**", (route) => route.fulfill({ json: [] }));
    await page.route("https://api.beacon.test/users/me", (route) => {
        identityRequests += 1;
        return route.fulfill({
            json: { user_id: 7, username: "uat-role-user", role: currentRole, agency_id: 1, is_active: true },
        });
    });
    await page.route("https://api.beacon.test/notifications/unread-count", (route) => route.fulfill({ json: { unread_count: 0 } }));
    await page.route("https://api.beacon.test/agencies/**", (route) => route.fulfill({ json: [] }));
    await page.route("https://api.beacon.test/agency-exchanges/**", (route) => route.fulfill({ json: [] }));
    await page.route("https://api.beacon.test/admin/users/**", (route) => route.fulfill({ json: [] }));
});

test("all supported roles receive the intended route boundary", async ({ page }) => {
    await page.goto("/agencies");
    await expect(page.getByRole("heading", { name: "Agency Management" })).toBeVisible();
    await expect(page.getByText("Controlled Agency Onboarding")).toBeVisible();

    await setRole(page, "agency_admin");
    await page.goto("/admin/users");
    await expect(page.getByRole("heading", { name: "User Management" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Access unavailable" })).toHaveCount(0);

    for (const [role, path] of [
        ["supervisor", "/admin/users"],
        ["investigator", "/supervisor"],
        ["analyst", "/evidence-upload"],
        ["viewer", "/intelligence"],
    ]) {
        await setRole(page, role);
        await page.goto(path);
        await expect(page.getByRole("heading", { name: "Access unavailable" })).toBeVisible();
    }

    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toEqual([]);
});

test("SPA navigation reuses one server identity verification", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Command Operations Center" })).toBeVisible();

    await page.getByRole("link", { name: "Cases", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Cases", exact: true })).toBeVisible();
    await page.getByRole("link", { name: "Missing Persons", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Missing Persons", exact: true })).toBeVisible();

    expect(identityRequests).toBe(1);
});
