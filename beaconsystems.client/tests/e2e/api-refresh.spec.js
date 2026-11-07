import { expect, test } from "@playwright/test";

const identity = {
    user_id: 17,
    username: "refresh-test-user",
    role: "analyst",
    agency_id: 1,
    is_active: true,
};

test("concurrent expired requests share one token refresh", async ({ page }) => {
    let refreshRequests = 0;
    const attempts = new Map();

    await page.addInitScript(() => {
        sessionStorage.setItem("token", "expired-access-token");
        sessionStorage.setItem("role", "analyst");
        sessionStorage.setItem("username", "refresh-test-user");
        sessionStorage.setItem("agency_id", "1");
        sessionStorage.setItem("last_activity_at", String(Date.now()));
        sessionStorage.setItem("session_expires_at", new Date(Date.now() + 3_600_000).toISOString());
    });

    await page.route("**/users/me", (route) => route.fulfill({ json: identity }));
    await page.route("**/dashboard/summary", (route) => route.fulfill({ json: {} }));
    await page.route("**/notifications/unread-count", (route) => route.fulfill({ json: { unread_count: 0 } }));
    await page.route("**/users/refresh", async (route) => {
        refreshRequests += 1;
        await new Promise((resolve) => setTimeout(resolve, 100));
        await route.fulfill({ json: {
            access_token: "rotated-access-token",
            session_expires_at: new Date(Date.now() + 3_600_000).toISOString(),
        } });
    });

    for (const pattern of [
        "**/sightings/",
        "**/external-records/",
        "**/bolos/",
        "**/evidence/",
        "**/persons/?limit=100",
        "**/matches/?limit=100",
    ]) {
        await page.route(pattern, (route) => {
            const url = route.request().url();
            const count = (attempts.get(url) || 0) + 1;
            attempts.set(url, count);
            return count === 1
                ? route.fulfill({ status: 401, json: { detail: "Token expired" } })
                : route.fulfill({ json: [] });
        });
    }

    await page.goto("/intelligence");
    await expect(page.getByRole("heading", { name: "Beacon Intelligence Center" })).toBeVisible();
    await expect.poll(() => [...attempts.values()].filter((count) => count === 2).length).toBe(6);
    await expect.poll(() => page.evaluate(() => sessionStorage.getItem("token")))
        .toBe("rotated-access-token");

    expect(refreshRequests).toBe(1);
});
