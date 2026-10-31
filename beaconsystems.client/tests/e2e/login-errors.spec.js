import { expect, test } from "@playwright/test";

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
        await page.route("https://api.beacon.test/users/login", (route) => route.fulfill({
            status: scenario.status,
            contentType: "application/json",
            body: JSON.stringify({ detail: scenario.detail }),
        }));

        await submitLogin(page);

        await expect(page.getByRole("alert")).toHaveText(scenario.message);
    });
}

test("login distinguishes an unreachable API from invalid credentials", async ({ page }) => {
    await page.route("https://api.beacon.test/users/login", (route) => route.abort("connectionrefused"));

    await submitLogin(page);

    await expect(page.getByRole("alert")).toContainText("Cannot reach Beacon");
});

test("login trims usernames and prevents duplicate submissions", async ({ page }) => {
    let requestCount = 0;
    let submittedUsername = null;
    await page.route("https://api.beacon.test/users/login", async (route) => {
        requestCount += 1;
        submittedUsername = route.request().postDataJSON().username;
        await new Promise((resolve) => setTimeout(resolve, 250));
        await route.fulfill({
            status: 401,
            contentType: "application/json",
            body: JSON.stringify({ detail: "Invalid credentials" }),
        });
    });

    await page.goto("/login");
    await page.getByLabel("Username").fill("  testsupervisor1  ");
    await page.getByLabel("Password").fill("not-a-real-password");
    const submit = page.getByRole("button", { name: "Secure Login" });
    await submit.dblclick();

    await expect(page.getByRole("button", { name: "Signing in…" })).toBeDisabled();
    await expect(page.getByRole("alert")).toHaveText("Invalid username or password.");
    expect(submittedUsername).toBe("testsupervisor1");
    expect(requestCount).toBe(1);
});
