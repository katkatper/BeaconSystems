import { expect, test } from "@playwright/test";

const CORS_HEADERS = {
    "access-control-allow-origin": "https://127.0.0.1:4173",
    "access-control-allow-credentials": "true",
    "access-control-allow-headers": "content-type, authorization",
    "access-control-allow-methods": "POST, PUT, OPTIONS",
};

async function handlePreflight(route) {
    if (route.request().method() !== "OPTIONS") return false;
    await route.fulfill({ status: 204, headers: CORS_HEADERS });
    return true;
}

async function submitLogin(page) {
    await page.goto("/login");
    await page.getByPlaceholder("Username").fill("testsupervisor1");
    await page.getByPlaceholder("Password").fill("not-a-real-password");
    await page.getByRole("button", { name: "Secure Login" }).click();
}

for (const scenario of [
    { status: 401, detail: "Invalid credentials", message: "Invalid username or password." },
    { status: 403, detail: "User account is inactive", message: "This account or agency is inactive. Contact your Beacon administrator." },
    { status: 404, detail: "Not Found", message: "Beacon's login service was not found. Confirm the frontend API address is configured." },
    { status: 429, detail: "Too many authentication attempts", message: "Too many sign-in attempts. Wait a few minutes and try again." },
    { status: 503, detail: "Authentication protection is temporarily unavailable", message: "Beacon authentication is temporarily unavailable. Try again shortly." },
]) {
    test(`login explains ${scenario.status} authentication failures`, async ({ page }) => {
        await page.route("https://api.beacon.test/users/login", async (route) => {
            if (await handlePreflight(route)) return;
            await route.fulfill({
            status: scenario.status,
            contentType: "application/json",
            headers: CORS_HEADERS,
            body: JSON.stringify({ detail: scenario.detail }),
            });
        });

        await submitLogin(page);

        await expect(page.getByRole("alert")).toHaveText(scenario.message);
    });
}

test("login distinguishes an unreachable API from invalid credentials", async ({ page }) => {
    await page.route("https://api.beacon.test/users/login", async (route) => {
        if (await handlePreflight(route)) return;
        await route.abort("connectionrefused");
    });

    await submitLogin(page);

    await expect(page.getByRole("alert")).toContainText("Cannot reach Beacon");
});

test("login trims accidental username whitespace", async ({ page, browserName }) => {
    test.skip(
        browserName === "webkit",
        "WebKit clears whitespace-padded autocomplete credentials before form submission.",
    );
    let submittedUsername = null;
    await page.route("https://api.beacon.test/users/login", async (route) => {
        if (await handlePreflight(route)) return;
        submittedUsername = route.request().postDataJSON().username;
        await route.fulfill({
            status: 401,
            contentType: "application/json",
            headers: CORS_HEADERS,
            body: JSON.stringify({ detail: "Invalid credentials" }),
        });
    });

    await page.goto("/login");
    const usernameInput = page.getByLabel("Username");
    await usernameInput.pressSequentially("  testsupervisor1  ");
    await expect(usernameInput).toHaveValue("  testsupervisor1  ");
    await page.getByRole("button", { name: "Secure Login" }).click();

    await expect(page.getByRole("alert")).toHaveText("Invalid username or password.");
    expect(submittedUsername).toBe("testsupervisor1");
});

test("login prevents duplicate submissions before the interface rerenders", async ({ page }) => {
    let requestCount = 0;
    await page.route("https://api.beacon.test/users/login", async (route) => {
        if (await handlePreflight(route)) return;
        requestCount += 1;
        await new Promise((resolve) => setTimeout(resolve, 250));
        await route.fulfill({
            status: 401,
            contentType: "application/json",
            headers: CORS_HEADERS,
            body: JSON.stringify({ detail: "Invalid credentials" }),
        });
    });

    await page.goto("/login");
    const submit = page.getByRole("button", { name: "Secure Login" });
    await submit.evaluate((button) => {
        button.form.requestSubmit();
        button.form.requestSubmit();
    });

    await expect(page.getByRole("button", { name: "Signing in…" })).toBeDisabled();
    await expect(page.getByRole("alert")).toHaveText("Invalid username or password.");
    expect(requestCount).toBe(1);
});
