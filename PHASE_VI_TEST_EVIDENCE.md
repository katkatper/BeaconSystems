# Phase VI automated test evidence

Date: October 24, 2026  
Environment: local Windows development workstation  
Data: synthetic mocked investigator workspace responses

## Passed matrix

Twelve Playwright scenarios passed across Chromium laptop (1366×768), WebKit
desktop, Chromium Android phone and Chromium iPad-sized tablet. Each profile
validated the investigator empty state, recoverable network failure and explicit
permission-denied state. Axe found no automated accessibility violations in the
tested workspace state.

The phone test initially found Beacon Insight blocking the retry action. Beacon
Insight now starts collapsed at 700px and below; the full four-profile rerun passed.

## Open evidence gates

- Firefox automation is configured but its binary could not launch on this host
  (`spawn UNKNOWN`). Execute it in CI or an approved browser lab before claiming
  Firefox support.
- Automated checks do not replace NVDA, VoiceOver or TalkBack testing.
- Human role-based UAT, current/previous real browser versions and agency sign-off
  remain pending in `USER_ACCEPTANCE_TEST_PLAN.md`.
