# Incident response plan and tabletop

Owner: designated Incident Commander.

1. Detect/declare: record severity, commander, secure channel and UTC timeline.
2. Preserve: protect logs/evidence and chain of custody.
3. Contain: revoke sessions/keys, suspend integrations/tenants, isolate safely.
4. Assess: determine data, agencies, people, jurisdictions and availability affected.
5. Notify: engage Security, Privacy/Legal, executives, insurer, vendors and agencies;
   counsel determines regulatory and individual notification.
6. Recover: eradicate cause, rotate secrets, restore trusted service and monitor.
7. Learn: root cause, corrective owners/dates and risk-register updates.

Do not copy credentials, raw CJI/ePHI or unnecessary personal data into tickets.

## Tabletop scenario

Monitoring reports anomalous cross-agency access by a supervisor while the worker
queue is delayed. A cloud vendor then reports possible token exposure. Injects:
public-records request, agency disconnect request, international source IP and a
failed audit-chain verification.

Record participants, declaration/containment times, affected scope, notification
decisions and authority, recovery/integrity proof, gaps, owners and deadlines.
Security, Operations, Privacy/Legal, Engineering, Communications and an agency
representative participate before production and annually.
