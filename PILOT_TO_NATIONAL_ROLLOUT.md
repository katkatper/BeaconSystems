# Pilot-to-national rollout plan

## Pilot entry

All automated release gates pass; staging exercises and penetration test close
critical/high findings; contracts and jurisdiction reviews are effective; monitoring,
support, backups, incident contacts and rollback are staffed; synthetic UAT passes.

## Controlled pilot

Start with one approved agency and bounded users/cases. Define duration, support
hours, success metrics and prohibited data. Review daily: availability, latency,
errors, queue age, security events, cross-tenant denials, alert delivery, support
volume and cost. Weekly: access, vulnerabilities, incidents and user feedback.

## Stop/rollback conditions

Cross-tenant exposure; audit-integrity failure; uncontained critical vulnerability;
loss of encryption/control plane; missed legal notification; unrecoverable evidence;
RPO/RTO breach; sustained service-level breach; agency or risk-owner direction.

## Expansion

Add agencies in cohorts only after prior cohort exit approval. Revalidate capacity,
support, residency, contracts, training and incident contacts for every cohort.
National availability requires Security, Operations, Privacy/Legal, Product and
participating-agency authorization in the controlled evidence system.
