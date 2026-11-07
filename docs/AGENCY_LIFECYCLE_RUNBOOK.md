# Agency lifecycle runbook

Agency lifecycle actions affect tenant access and require an approved request,
platform administrator, independent reviewer and retained audit evidence. Do not
create agencies from public directory listings alone; verify legal authority and
the requesting organization through an approved channel.

## Onboarding

1. Record the agency's legal name, jurisdiction, authority, primary and security
   contacts, data classifications, expected scale, region and applicable CJIS/HIPAA
   responsibilities.
2. Obtain privacy/legal, security and participating-agency approval.
3. Create the agency with a platform administrator. Duplicate names are rejected.
4. Create the initial agency administrator with a temporary password delivered by
   an approved separate channel. Require password change and MFA enrollment.
5. Verify least-privilege roles, tenant isolation, logging, alert routing, retention
   policy, support contacts and training before allowing production records.
6. Record the agency ID and evidence links without copying protected data.

## Suspension

Use suspension for a security incident, expired authorization, contract hold or
other approved temporary stop. Provide a specific reason. Beacon immediately
disables every agency user, increments authentication versions and revokes active
sessions. Reactivation does not automatically reactivate users; administrators must
review and enable each account deliberately after approval.

The acting platform administrator cannot suspend their own agency. Use a separate
authorized platform administrator and reviewer. Verify the audit event and monitor
for rejected access attempts after suspension.

## Offboarding

Offboarding is terminal in Beacon. Confirm legal hold, retention, evidence custody,
open cross-agency work, exports, contracts and notification duties before changing
the status. Beacon disables access but does not delete investigative records.
Disposition occurs only under approved records policy and legal authority. A former
agency returning later receives a newly approved tenant rather than reactivation.
