# Finalization checkpoint — 2026-10-23

Status: implementation candidate; browser/live acceptance and deployment pending. This record supplements, and does not rewrite, the approved Skill Pack artifacts or completed 5-build milestones.

## Authorized delivery change
Web remains the complete live standalone product. Gemini browser integration now uses explicit Check this answer, with no automatic POST completion inference. Composer review, user-approved edits, unchanged original submission, evidence-based answer review and manually placed targeted repair drafts reuse shared core functions. The failed lifecycle spike remains preserved as evidence.

## Implemented candidate
- extensions/browser: MV3 Gemini adapter, composer interception, explicit request improvement acceptance, explicit answer review, four-state findings/evidence and targeted repair drafting. No automatic follow-up submission. Worker pins its backend, validates sender and response shape, and stores only the bounded pass in trusted extension storage.
- app/web/browser_api.py: PRE, explicit POST and NEXT using shared core/provider contracts. POST extracts from the exact selected host request before evaluating (two calls); no unaccepted PRE proposal is canonicalized. Browser review results are page-local, not Web History.
- Judge Pass: hashed opaque tokens, expiration, atomic SQLite per-call reservations, pass allowance, rolling-minute limit, persistent global lifetime circuit breaker. Attempts are charged before provider calls; failed attempts remain charged. Web History and APIs require a valid pass. Web uses HttpOnly SameSite=Strict cookie and checks mutation Origin; extension uses Bearer without cookies.
- Defaults: operator-issued 30 operations / 72 hours, 6 calls/minute/pass, global 200 calls. Each provider context <=60,000 serialized characters, output <=6,000 tokens. Configuration controls call limits; this is not exact dollar billing. Global zero disables reservations. Pass ledger must survive restart and deployment.
- Shared controlled Web History is disclosed at access and in README. No accounts or multi-user isolation. Server-side model credentials remain outside Git.
- Minimal glasses identity; single-origin HTTPS ZIP packaging utility; operator and judge installation/privacy documentation.

## Verification
91 Python tests passed. New tests cover invalid/expired/exhausted access, concurrency, rate limits, restart, failed reservations, protected History, cookie-origin checks, explicit browser API and restricted package generation. Node worker protocol checks passed without network. JavaScript syntax and whitespace checks passed.
Replay SHA-256: 75dcd41aea1591ccce90e5dff4307b6680a974bdb9872e56f6374aea297794e3 (unchanged).
No new OpenAI or Gemini inference performed. Read-only real Gemini inspection confirmed .query-text-line excludes hidden duplicate headings. The old probe is still enabled; new extension has not yet been installed or browser-validated. Do not present unit tests as browser acceptance.

## Next validation gate
Request authorization for at most six OpenAI calls and one normal Gemini generation: Web PRE/answer/POST (3); extension PRE (1), exact-request extraction + POST (2). No retry for a more interesting outcome; no live repair call in this batch. Invalid/exhausted access is already verified deterministically and must cause zero provider calls. Record actual usage/results and stop on a blocker.

The public HTTPS origin has not been selected/verified in repository evidence. Deployment and judge ZIP must use one confirmed VESTA origin; source extension points to loopback for local validation only. The operator/judge installation has no need for Google credentials from us or an OpenAI key. Chrome load-unpacked and disabling the old probe require user interaction.

6-ship has been read but not started: final live/browser validation is required first. Its existing requirements remain video, public repository, learner-written submission fields and exit survey. No submission/publication claim has been made.

## User-authored shipping thesis (preserve verbatim)
“Did the AI actually deliver what you asked for — and if not, can you fix only what is missing?”
“Most tools optimize the request or evaluate the model. PickyLens supervises the interaction end to end.”
“PickyLens checks whether the AI actually delivered what you asked for — and fixes only what’s missing.”
Working product first in the demo; no long trailer or architecture preamble.
