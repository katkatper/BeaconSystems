import { expect, test } from "@playwright/test";

test("an invited user can reach and submit account registration", async ({ page }) => {
    await page.route("**/onboarding/register", async (route) => {
        expect(route.request().postDataJSON()).toMatchObject({ username: "invited-staff" });
        await route.fulfill({ status: 201, json: { message: "Account created. You can now sign in." } });
    });
    await page.goto("/login");
    await page.getByRole("link", { name: "Create Account", exact: true }).click();
    await page.getByLabel("Invitation code").fill("a".repeat(43));
    await page.getByLabel("Username").fill("invited-staff");
    await page.getByLabel("Password").fill("sample-password-only");
    await page.getByRole("button", { name: "Create account" }).click();
    await expect(page.getByRole("status")).toHaveText("Account created. You can now sign in.");
});

test("an applicant can submit a request without receiving an account", async ({ page }) => {
    await page.route("**/onboarding/access-requests", async (route) => {
        expect(route.request().postDataJSON()).toEqual({
            email: "applicant@example.com", agency_name: "Example Agency",
        });
        await route.fulfill({ status: 202, json: { message: "Your request has been received for review." } });
    });
    await page.goto("/login");
    await page.getByRole("link", { name: "Request access" }).click();
    await page.getByLabel("Work email").fill("applicant@example.com");
    await page.getByLabel("Agency name").fill("Example Agency");
    await page.getByRole("button", { name: "Send request" }).click();
    await expect(page.getByRole("status")).toHaveText("Your request has been received for review.");
});
