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

test("a rejected refresh does not loop or replace the expired token", async ({ page }) => {
    let refreshRequests = 0;
    let dataRequests = 0;

    await seedSession(page);
    await mockIntelligenceShell(page);
    await page.route("**/users/refresh", (route) => {
        refreshRequests += 1;
        return route.fulfill({ status: 401, json: { detail: "Refresh expired" } });
    });
    await page.route("**/sightings/", (route) => {
        dataRequests += 1;
        return route.fulfill({ status: 401, json: { detail: "Token expired" } });
    });
    await mockOtherIntelligenceRequests(page);

    await page.goto("/intelligence");
    await expect.poll(() => dataRequests).toBeGreaterThan(0);
    await page.waitForTimeout(250);
    expect(refreshRequests).toBe(1);
    expect(dataRequests).toBe(2);
    const settledRequests = dataRequests;
    await page.waitForTimeout(250);
    expect(dataRequests).toBe(settledRequests);
    await expect.poll(() => page.evaluate(() => sessionStorage.getItem("token")))
        .toBe("expired-access-token");
});

test("a refreshed request that is still unauthorized is not retried again", async ({ page }) => {
    let refreshRequests = 0;
    let dataRequests = 0;

    await seedSession(page);
    await mockIntelligenceShell(page);
    await page.route("**/users/refresh", (route) => {
        refreshRequests += 1;
        return route.fulfill({ json: {
            access_token: "rotated-access-token",
            session_expires_at: new Date(Date.now() + 3_600_000).toISOString(),
        } });
    });
    await page.route("**/sightings/", (route) => {
        dataRequests += 1;
        return route.fulfill({ status: 401, json: { detail: "Unauthorized" } });
    });
    await mockOtherIntelligenceRequests(page);

    await page.goto("/intelligence");
    await expect.poll(() => refreshRequests).toBeGreaterThan(0);
    await page.waitForTimeout(250);
    expect(refreshRequests).toBe(1);
    expect(dataRequests).toBe(4);
    const settledRequests = dataRequests;
    await page.waitForTimeout(250);
    expect(dataRequests).toBe(settledRequests);
});

test("logout during a pending refresh cannot restore the old session", async ({ page }) => {
    let releaseRefresh = null;

    await seedSession(page);
    await mockIntelligenceShell(page);
    await page.route("**/users/refresh", async (route) => {
        await new Promise((resolve) => {
            releaseRefresh = () => {
                resolve();
                releaseRefresh = null;
            };
        });
        return route.fulfill({ json: {
            access_token: "must-not-be-restored",
            session_expires_at: new Date(Date.now() + 3_600_000).toISOString(),
        } });
    });
    await page.route("**/sightings/", (route) => (
        route.fulfill({ status: 401, json: { detail: "Token expired" } })
    ));
    await mockOtherIntelligenceRequests(page);

    await page.goto("/intelligence");
    await expect.poll(() => Boolean(releaseRefresh)).toBe(true);
    await page.evaluate(() => sessionStorage.clear());
    releaseRefresh();
    await expect.poll(() => page.evaluate(() => sessionStorage.getItem("token"))).toBeNull();
});

async function seedSession(page) {
    await page.addInitScript(() => {
        sessionStorage.setItem("token", "expired-access-token");
        sessionStorage.setItem("role", "analyst");
        sessionStorage.setItem("username", "refresh-test-user");
        sessionStorage.setItem("agency_id", "1");
        sessionStorage.setItem("last_activity_at", String(Date.now()));
        sessionStorage.setItem("session_expires_at", new Date(Date.now() + 3_600_000).toISOString());
    });
}

async function mockIntelligenceShell(page) {
    await page.route("**/users/me", (route) => route.fulfill({ json: identity }));
    await page.route("**/dashboard/summary", (route) => route.fulfill({ json: {} }));
    await page.route("**/notifications/unread-count", (route) => (
        route.fulfill({ json: { unread_count: 0 } })
    ));
}

async function mockOtherIntelligenceRequests(page) {
    for (const pattern of [
        "**/external-records/",
        "**/bolos/",
        "**/evidence/",
        "**/persons/?limit=100",
        "**/matches/?limit=100",
    ]) {
        await page.route(pattern, (route) => route.fulfill({ json: [] }));
    }
}
