# Production acceptance exercise packet

Use synthetic data unless the approved exercise plan explicitly authorizes otherwise.
For every exercise record date/time UTC, commit/image, environment, participants,
expected result, actual result, evidence links, defects, owner/due date and approval.
Never paste credentials, keys, CJI, ePHI or unredacted personal information.

## Required exercises

1. Incident tabletop: execute `INCIDENT_RESPONSE_TABLETOP.md`; measure declaration,
   containment, notification decision and trusted recovery.
2. Access review/termination: review all roles, revoke a synthetic account and prove
   its existing session and restricted routes fail.
3. Agency lifecycle: onboard, suspend, reactivate and offboard a synthetic agency;
   verify tenant isolation, session revocation and audit events.
4. Audit integrity: export an immutable copy, run `scripts/verify_audit_integrity.py`,
   alter a disposable copy and prove verification fails.
5. Backup/recovery/failover: follow the Phase IV runbooks, record measured RPO/RTO,
   integrity verification and service recovery.
6. Key rotation: rotate application, audit-HMAC, MFA, storage and integration keys
   one class at a time; prove old access fails and new access succeeds.
7. Role UAT/accessibility: execute `USER_ACCEPTANCE_TEST_PLAN.md` with every role and
   NVDA, VoiceOver and TalkBack as applicable.
8. Independent penetration test: approved third party tests the deployed scope;
   critical/high findings are remediated or formally rejected by the risk owner.

Copy `config/assurance_evidence_template.json` into the controlled evidence system,
replace pending fields, and run:

`python scripts/validate_assurance_evidence.py record.json --require-complete`

The validator checks completeness only. It does not prove evidence is authentic or
authorize a release; designated reviewers must inspect and sign the referenced proof.
