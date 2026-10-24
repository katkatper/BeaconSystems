# Access review, transfer and termination

Owner: IAM Administrator; reviewer: agency security administrator.

- Quarterly: all accounts, roles, agency membership, service and privileged access.
- Monthly: platform admins, break-glass access, dormant accounts and exceptions.
- Event-driven: transfer, leave, contract end, compromise or agency suspension.

Review employment/sponsorship, agency, role, case need, MFA and last use. Nobody
approves their own access. Compromise/involuntary termination and agency suspension
require immediate revocation; planned termination is complete by its effective time;
transfers are adjusted before new duties; unresolved reviews suspend in five days.

Checklist: disable identity; revoke sessions/tokens; remove roles, assignments,
API/service and physical access; rotate shared secrets; preserve required records;
recover equipment; notify agency; test denied access; record approver, actor, UTC
time and audit IDs. Emergency access is time-limited, approved, monitored and
reviewed the next business day.
