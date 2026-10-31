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

test("investigator receives a private case access-denied state", async ({ page }) => {
    await page.route("https://api.beacon.test/cases/41", (route) =>
        route.fulfill({ status: 403, json: { detail: "Case access is not authorized" } })
    );
    await page.goto("/cases/41");

    await expect(page.getByRole("heading", { name: "You cannot access this case" })).toBeVisible();
    await expect(page.getByText("Case access is not authorized")).toBeVisible();
    await expect(page.getByRole("button", { name: "Try again" })).toHaveCount(0);
    await expect(page.getByRole("link", { name: "Return to authorized cases" })).toBeVisible();

    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toEqual([]);
});

test("investigator can retry a temporarily unavailable case", async ({ page }) => {
    let attempts = 0;
    await page.route("https://api.beacon.test/cases/41", (route) => {
        attempts += 1;
        // React StrictMode invokes the initial effect twice in development.
        if (attempts <= 2) {
            return route.fulfill({ status: 503, json: { detail: "Case service is recovering" } });
        }
        return route.fulfill({
            json: {
                case_id: 41,
                case_number: "MP-TEST-0041",
                title: "Synthetic case",
                person_id: 19,
                status: "open",
            },
        });
    });
    for (const endpoint of [
        "https://api.beacon.test/sightings/**",
        "https://api.beacon.test/timeline-events/**",
        "https://api.beacon.test/evidence/case/**",
        "https://api.beacon.test/persons/**",
        "https://api.beacon.test/external-records/**",
        "https://api.beacon.test/agency-exchanges/**",
        "https://api.beacon.test/cases/41/correlations",
        "https://api.beacon.test/leads/**",
    ]) {
        await page.route(endpoint, (route) => route.fulfill({ json: [] }));
    }
    await page.goto("/cases/41");

    await expect(page.getByRole("heading", { name: "Case details could not load" })).toBeVisible();
    await page.getByRole("button", { name: "Try again" }).click();
    await expect(page.getByText("MP-TEST-0041")).toBeVisible();
});

test("investigator sees partial-data warnings and immutable evidence status", async ({ page }) => {
    await page.route("https://api.beacon.test/cases/41", (route) => route.fulfill({
        json: {
            case_id: 41,
            case_number: "MP-TEST-0041",
            title: "Synthetic case",
            person_id: 19,
            case_status: "open",
            priority_level: "high",
            agency_id: 4,
            investigator_id: 8,
        },
    }));
    await page.route("https://api.beacon.test/evidence/case/41", (route) => route.fulfill({
        json: [{
            evidence_id: 71,
            evidence_type: "photo_video",
            description: "Synthetic camera image",
            file_name: "camera.jpg",
            is_sensitive: true,
            has_preview: false,
            storage_tier: "archived",
            content_sha256: "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        }],
    }));
    await page.route("https://api.beacon.test/timeline-events/**", (route) =>
        route.fulfill({ status: 503, json: { detail: "Timeline temporarily unavailable" } })
    );
    await page.route("https://api.beacon.test/evidence/chain/71", (route) => route.fulfill({
        json: [{ chain_id: 1, action: "UPLOAD_EVIDENCE", details: "Original recorded", created_at: "2026-10-31T12:00:00Z" }],
    }));
    for (const endpoint of [
        "https://api.beacon.test/sightings/**",
        "https://api.beacon.test/persons/**",
        "https://api.beacon.test/external-records/**",
        "https://api.beacon.test/agency-exchanges/**",
        "https://api.beacon.test/leads/**",
    ]) {
        await page.route(endpoint, (route) => route.fulfill({ json: [] }));
    }
    await page.route("https://api.beacon.test/cases/41/correlations", (route) =>
        route.fulfill({ json: { correlations: [] } })
    );
    await page.goto("/cases/41");

    await expect(page.getByText(/could not load: timeline/i)).toBeVisible();
    await page.getByRole("tab", { name: "Evidence" }).click();
    await expect(page.getByText("Synthetic camera image")).toBeVisible();
    await expect(page.getByText(/SHA-256 abcdef123456/)).toBeVisible();
    await expect(page.getByRole("button", { name: "Archived" })).toBeDisabled();
    await expect(page.getByRole("button", { name: "Archive original" })).toHaveCount(0);
    await page.getByRole("button", { name: "View Chain of Custody" }).click();
    await expect(page.getByText("Original recorded")).toBeVisible();
});

test("investigator documents lead resolution and confirms sighting removal", async ({ page }) => {
    let submittedResolution = null;
    let deletedSighting = false;
    await page.route("https://api.beacon.test/cases/41", (route) => route.fulfill({
        json: {
            case_id: 41,
            case_number: "MP-TEST-0041",
            person_id: 19,
            case_status: "open",
            priority_level: "high",
            agency_id: 4,
            investigator_id: 8,
        },
    }));
    await page.route("https://api.beacon.test/sightings/**", async (route) => {
        if (route.request().method() === "DELETE") {
            deletedSighting = true;
            return route.fulfill({ json: { message: "removed" } });
        }
        return route.fulfill({ json: [{ sighting_id: 51, location: "Synthetic station", description: "Test sighting" }] });
    });
    await page.route("https://api.beacon.test/leads/**", async (route) => {
        if (route.request().method() === "PUT") {
            const requestData = route.request().postDataJSON();
            submittedResolution = requestData.resolution;
            return route.fulfill({ json: {
                lead_id: 61,
                lead_source: "Camera review",
                description: "Review synthetic footage",
                priority: "high",
                status: requestData.status,
                resolution: requestData.resolution,
            } });
        }
        if (route.request().url().includes("/assignees")) return route.fulfill({ json: [] });
        return route.fulfill({ json: [{
            lead_id: 61,
            lead_source: "Camera review",
            description: "Review synthetic footage",
            priority: "high",
            status: "in_progress",
        }] });
    });
    await page.route("https://api.beacon.test/persons/**", (route) => route.fulfill({ json: { person_id: 19, known_associates: "" } }));
    for (const endpoint of [
        "https://api.beacon.test/timeline-events/**",
        "https://api.beacon.test/evidence/case/**",
        "https://api.beacon.test/external-records/**",
        "https://api.beacon.test/agency-exchanges/**",
    ]) {
        await page.route(endpoint, (route) => route.fulfill({ json: [] }));
    }
    await page.route("https://api.beacon.test/cases/41/correlations", (route) => route.fulfill({ json: { correlations: [] } }));
    await page.goto("/cases/41");

    await page.getByRole("tab", { name: "Leads" }).click();
    const leadCard = page.locator(".case-lead-card").filter({ hasText: "Camera review" });
    await leadCard.getByLabel("Status").selectOption("resolved");
    const resolutionDialog = page.getByRole("dialog", { name: "Document lead resolution" });
    await expect(resolutionDialog).toBeVisible();
    await resolutionDialog.getByLabel("Resolution summary").fill("Footage reviewed; no confirmed match.");
    await resolutionDialog.getByRole("button", { name: "Save resolution" }).click();
    await expect(leadCard.getByText(/Footage reviewed/)).toBeVisible();
    expect(submittedResolution).toBe("Footage reviewed; no confirmed match.");

    await page.getByRole("tab", { name: "Sightings" }).click();
    await page.getByRole("button", { name: "Remove" }).click();
    const removalDialog = page.getByRole("alertdialog", { name: "Remove this sighting?" });
    await expect(removalDialog).toBeVisible();
    await removalDialog.getByRole("button", { name: "Remove sighting" }).click();
    await expect(page.getByText("Sighting removed.")).toBeVisible();
    expect(deletedSighting).toBe(true);
});
