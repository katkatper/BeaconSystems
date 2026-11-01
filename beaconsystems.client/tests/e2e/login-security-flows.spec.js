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

async function beginLogin(page, response) {
    await page.route("https://api.beacon.test/users/login", async (route) => {
        if (await handlePreflight(route)) return;
        await route.fulfill({ json: response, headers: CORS_HEADERS });
    });
    await page.goto("/login");
    await page.getByLabel("Username").fill("testsupervisor1");
    await page.getByLabel("Password").fill("synthetic-password");
    await page.getByRole("button", { name: "Secure Login" }).click();
}

test("MFA verification prevents duplicate security requests", async ({ page }) => {
    let verificationRequests = 0;
    await page.route("https://api.beacon.test/users/mfa/verify", async (route) => {
        if (await handlePreflight(route)) return;
        verificationRequests += 1;
        await new Promise((resolve) => setTimeout(resolve, 250));
        await route.fulfill({ status: 400, json: { detail: "Invalid MFA code" }, headers: CORS_HEADERS });
    });
    await beginLogin(page, { mfa_required: true, mfa_token: "synthetic-mfa-token" });

    await page.getByLabel("MFA verification code").fill("123456");
    await page.getByRole("button", { name: "Verify Code" }).dblclick();

    await expect(page.getByRole("button", { name: "Verifying…" })).toBeDisabled();
    await expect(page.getByRole("alert")).toHaveText("Invalid MFA code");
    expect(verificationRequests).toBe(1);
});

test("MFA enrollment prevents duplicate security requests", async ({ page }) => {
    let enrollmentRequests = 0;
    await page.route("https://api.beacon.test/users/mfa/enrollment/start", async (route) => {
        if (await handlePreflight(route)) return;
        await route.fulfill({ json: {
            issuer: "Beacon",
            account: "testsupervisor1",
            secret: "SYNTHETICSECRET",
            otpauth_uri: "otpauth://totp/Beacon:testsupervisor1?secret=SYNTHETICSECRET",
        }, headers: CORS_HEADERS });
    });
    await page.route("https://api.beacon.test/users/mfa/enrollment/complete", async (route) => {
        if (await handlePreflight(route)) return;
        enrollmentRequests += 1;
        await new Promise((resolve) => setTimeout(resolve, 250));
        await route.fulfill({ status: 400, json: { detail: "Invalid MFA code" }, headers: CORS_HEADERS });
    });
    await beginLogin(page, { mfa_enrollment_required: true, mfa_token: "synthetic-enrollment-token" });

    await page.getByLabel("Authenticator verification code").fill("123456");
    await page.getByRole("button", { name: "Enable MFA and Sign In" }).dblclick();

    await expect(page.getByRole("button", { name: "Enabling MFA…" })).toBeDisabled();
    await expect(page.getByRole("alert")).toHaveText("Invalid MFA code");
    expect(enrollmentRequests).toBe(1);
});

test("required password update prevents duplicate security requests", async ({ page }) => {
    let updateRequests = 0;
    await page.route("https://api.beacon.test/users/change-password", async (route) => {
        if (await handlePreflight(route)) return;
        updateRequests += 1;
        await new Promise((resolve) => setTimeout(resolve, 250));
        await route.fulfill({ status: 400, json: { detail: "Password does not meet policy" }, headers: CORS_HEADERS });
    });
    await beginLogin(page, {
        access_token: "synthetic-access-token",
        role: "supervisor",
        username: "testsupervisor1",
        agency_id: 1,
        password_change_required: true,
    });

    await page.getByLabel("New password", { exact: true }).fill("Synthetic-password-2026");
    await page.getByLabel("Confirm new password", { exact: true }).fill("Synthetic-password-2026");
    await page.getByRole("button", { name: "Update Password" }).dblclick();

    await expect(page.getByRole("button", { name: "Updating password…" })).toBeDisabled();
    await expect(page.getByRole("alert")).toHaveText("Password does not meet policy");
    expect(updateRequests).toBe(1);
});
