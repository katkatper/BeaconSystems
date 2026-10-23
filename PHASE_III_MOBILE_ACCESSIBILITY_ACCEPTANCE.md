+# Phase III mobile and accessibility acceptance

Automated lint, build and contract checks are prerequisites, not proof of browser
or assistive-technology acceptance. Complete this matrix against a production-like
PostgreSQL staging deployment with representative, non-production case data.

## Required environments

| Environment | Minimum acceptance target |
| --- | --- |
| Windows | Current Chrome, Edge, Firefox; keyboard-only; NVDA with Chrome or Firefox |
| macOS | Current Safari and Chrome; keyboard-only; VoiceOver with Safari |
| iOS | Current Safari on an iPhone-sized viewport; VoiceOver |
| Android | Current Chrome on a phone-sized viewport; TalkBack |
| Tablet | Current Safari or Chrome in portrait and landscape |

Record browser, operating-system and assistive-technology versions with the test
date. A failed critical workflow blocks Phase III release acceptance.

## Investigator critical-flow checks

- Sign in, reach Investigator Workspace and sign out without a pointer.
- Use the skip link and confirm focus enters the main workspace.
- Open an assigned case and move through case tabs in a predictable order.
- Review an urgent alert and return to the originating case.
- Open, read and mark an investigator notification read; confirm the unread count
  changes and remains read after signing in on another browser.
- Review a generated match, enter a disposition reason and confirm the decision.
- Upload evidence using labels, validation messages and keyboard controls.
- At 320 CSS pixels wide, complete each flow without page-level horizontal loss;
  data tables may scroll inside their own region.
- At 200% browser zoom, content and controls remain available without overlap.
- With reduced motion enabled, no essential status depends on animation.
- With forced colors or increased contrast enabled, focus and unread states remain
  distinguishable without color alone.

## Acceptance evidence

For every environment, record pass/fail, tester, date, defects and links to captured
evidence. Critical and high-severity findings must be resolved and retested. Medium
findings require a documented release decision; low findings may enter the backlog.

Phase III is accepted only when all critical flows pass in every required environment
and the product owner and accessibility reviewer approve the recorded evidence.
