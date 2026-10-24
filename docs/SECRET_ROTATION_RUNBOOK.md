# Secret and key rotation runbook

Production values belong in the deployment secret manager, never source control or
container images. Maintain named owners and rotation schedules for database roles,
`SECRET_KEY`, `MFA_SECRET_ENCRYPTION_KEY`, `BEACON_CASE_ACCESS_CODE`, Redis,
partner webhook, Splunk, ArcGIS, object-storage roles, `AUDIT_INTEGRITY_KEY` and
the KMS key.

## Safe rotation rules

- Create and validate replacement credentials before revoking the prior value when
  the provider supports overlap.
- Rotate one dependency at a time and monitor authentication, readiness and audit
  delivery before proceeding.
- Changing `SECRET_KEY` invalidates existing access tokens. Schedule the change,
  revoke durable sessions and require users to sign in with MFA again.
- Do not replace `MFA_SECRET_ENCRYPTION_KEY` in place: existing enrolled secrets
  cannot be decrypted afterward. Use an approved re-encryption migration or require
  controlled MFA re-enrollment before retiring the old key.
- Rotate `BEACON_CASE_ACCESS_CODE` after suspected exposure and review access logs.
- KMS rotation must preserve decrypt permission for retained evidence versions.
- Audit-integrity rotation requires a new `AUDIT_INTEGRITY_KEY_ID`; retain prior
  key versions in the verifier's approved secret source for the full audit period.
- Record secret identifier/version, never the secret value, in evidence.

Emergency rotation requires an incident record, two-person review for privileged
keys, validation of dependent services, revocation of the old value, and a follow-up
audit for unexpected use.
