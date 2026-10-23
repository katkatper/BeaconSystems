# Incident response runbook

## Activate

Open an incident when confidentiality, integrity, availability, tenant isolation,
authentication, evidence custody, external delivery or audit collection may be
affected. Assign an incident commander, operations lead, security lead,
communications lead and recorder. Use approved out-of-band communications if the
Beacon environment may be compromised.

## First actions

1. Record detection time, reporter, affected environment and request identifiers.
2. Protect life-safety operations; communicate unavailable workflows to agencies.
3. Contain with the narrowest reversible control. Do not erase hosts or logs.
4. Revoke affected sessions, credentials or integrations when authorized.
5. Preserve centralized audit, application, database, KMS and cloud-control logs.
6. Determine affected agencies and data classes without copying sensitive records
   into tickets or chat.
7. Engage privacy/legal and the participating agency/CJIS authority according to
   approved notification matrices. Engineering does not decide notification duties.

## Recover and close

Recover through the deployment or backup runbook, validate tenant boundaries and
chain of custody, monitor for recurrence, and obtain incident-commander approval.
Document root cause, timeline, scope, control failures, corrective actions, owners
and dates. Legal determines retention and external notification evidence.
