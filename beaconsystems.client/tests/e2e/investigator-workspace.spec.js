import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const emptyWorkspace = {
    assigned_cases: [],
    urgent_alerts: [],
    pending_leads: [],
    unread_notifications: [],
    has_more: {
        assigned_cases: false,
        urgent_alerts: false,
        pending_leads: false,
        unread_notifications: false,
    },
};

async function authenticateInvestigator(page) {
    await page.addInitScript(() => {
        localStorage.setItem("token", "synthetic-browser-test-token");
        localStorage.setItem("role", "investigator");
        localStorage.setItem("username", "uat-investigator");
        localStorage.setItem("last_activity_at", String(Date.now()));
        localStorage.setItem("session_expires_at", new Date(Date.now() + 3_600_000).toISOString());
    });
}

test.beforeEach(async ({ page }) => {
    await authenticateInvestigator(page);
    await page.route("**/dashboard/summary", (route) => route.fulfill({ json: {} }));
    await page.route("**/notifications/unread-count", (route) => route.fulfill({ json: { unread_count: 0 } }));
});

test("investigator empty state is responsive and accessible", async ({ page }) => {
    await page.route("**/dashboard/investigator", (route) => route.fulfill({ json: emptyWorkspace }));
    await page.goto("/");

    await expect(page.getByRole("heading", { name: "Investigator Workspace" })).toBeVisible();
    await expect(page.getByText("No active cases are assigned to you.")).toBeVisible();
    await expect(page.getByText("You are caught up.")).toBeVisible();
    await expect(page.locator("body")).not.toHaveCSS("overflow-x", "scroll");

    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toEqual([]);
});

test("investigator can retry a failed workspace request", async ({ page }) => {
    let attempts = 0;
    await page.route("**/dashboard/investigator", (route) => {
        attempts += 1;
        // React StrictMode invokes the initial effect twice in development.
        if (attempts <= 2) {
            return route.fulfill({ status: 503, json: { detail: "Service temporarily unavailable" } });
        }
        return route.fulfill({ json: emptyWorkspace });
    });
    await page.goto("/");

    await expect(page.getByRole("heading", { name: "Workspace could not refresh" })).toBeVisible();
    await page.getByRole("button", { name: "Try again" }).click();
    await expect(page.getByText("No active cases are assigned to you.")).toBeVisible();
});

test("investigator sees a permission-specific denied state", async ({ page }) => {
    await page.route("**/dashboard/investigator", (route) =>
        route.fulfill({ status: 403, json: { detail: "Insufficient permissions" } })
    );
    await page.goto("/");

    await expect(page.getByRole("heading", { name: "Workspace access unavailable" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Try again" })).toHaveCount(0);
});

test("viewer is denied restricted administration before data loads", async ({ page }) => {
    let restrictedRequests = 0;
    await page.route("https://api.beacon.test/admin/users**", (route) => {
        restrictedRequests += 1;
        return route.abort();
    });
    await page.goto("/");
    await page.evaluate(() => localStorage.setItem("role", "viewer"));
    await page.goto("/admin/users");

    await expect(page.getByRole("heading", { name: "Access unavailable" })).toBeVisible();
    await expect(page.getByText("No restricted data was loaded.", { exact: false })).toBeVisible();
    expect(restrictedRequests).toBe(0);

    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toEqual([]);
});

test("investigator reviews assigned operational work and clears a notification", async ({ page }) => {
    const workspace = {
        assigned_cases: [{ case_id: 41, case_number: "MP-TEST-0041", title: "Synthetic case", priority: "high", status: "Open" }],
        urgent_alerts: [{ alert_id: 7, case_id: 41, title: "Synthetic urgent alert", severity: "critical" }],
        pending_leads: [{ lead_id: 9, case_id: 41, priority: "high", status: "new", due_at: "2026-10-26T15:00:00Z" }],
        unread_notifications: [{ notification_id: 12, case_id: 41, title: "Lead assigned", message: "Review the synthetic lead." }],
        has_more: { assigned_cases: false, urgent_alerts: false, pending_leads: false, unread_notifications: false },
    };
    await page.route("**/dashboard/investigator", (route) => route.fulfill({ json: workspace }));
    await page.route("**/notifications/12/read", (route) => route.fulfill({ json: { status: "read" } }));
    await page.goto("/");

    await expect(page.getByRole("link", { name: /MP-TEST-0041/ })).toBeVisible();
    await expect(page.getByRole("link", { name: "Synthetic urgent alert" })).toBeVisible();
    await expect(page.getByRole("link", { name: /Lead 9/ })).toBeVisible();
    await page.getByRole("button", { name: "Mark read" }).click();
    await expect(page.getByText("Notification marked read.")).toBeAttached();
    await expect(page.getByText("You are caught up.")).toBeVisible();
});
