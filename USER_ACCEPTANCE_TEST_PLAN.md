# Beacon role and operational acceptance plan

Owner: Product Operations; witnesses: Security and participating agency.
Use synthetic records. Record commit, environment, browser/viewport, role, tester,
UTC time, expected/actual result, evidence and defect ID.

| Scenario | Roles | Status |
|---|---|---|
| Sign in, MFA, idle/absolute timeout, sign out | All | Pending execution |
| Create/assign case; verify tenant boundary | Supervisor, investigator | Pending |
| Review lead, upload evidence, receive notification | Investigator | Pending |
| Create/approve alert/BOLO; inspect impact/receipts | Supervisor | Pending |
| Search names then deliberately open missing-person profile | Authorized roles | Pending |
| Request/approve cross-agency access | Investigator, supervisor/admin | Pending |
| Provision/suspend/reactivate/offboard agency/users | Platform/agency admin | Pending |
| Verify viewer cannot mutate/use administration | Viewer | Pending |
| Empty/loading/denied/network failure/retry | All | Pending |
| Keyboard-only, 200% zoom, screen-reader names/live status | All | Pending |

Launch matrix: current/previous Chrome, Edge and Firefox; current Safari; 360×800,
768×1024, 1366×768 and 1920×1080. Claims require real browser/device or approved
cloud-lab execution. Release requires no critical/high defects and Product, Security,
Accessibility and agency acceptance.
