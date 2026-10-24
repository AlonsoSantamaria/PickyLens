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

## Authorized live validation — 2026-10-23

Canonical VESTA hostname approved by learner: https://pickylens.neovantia.live (same-origin API). Deployment has not yet occurred.

Web live API acceptance passed with no retries or repair: PRE green; POST 5 complete, 0 partial, 0 missing, 0 needs_review. History endpoint and public no-Replay page checks passed. This is API acceptance, not a claim of a completed browser hands-on review.

| Call | Purpose | Model | Effort | Input | Output | Reasoning tokens (included in output) | Total | Duration ms |
|---|---|---|---|---:|---:|---:|---:|---:|
| 1 | PRE | gpt-5.6-sol | low | 377 | 232 | 0 | 609 | 4708.94 |
| 2 | Web answer | gpt-5.6-sol | low | 47 | 186 | 23 | 233 | 4150.50 |
| 3 | POST | gpt-5.6-sol | low | 1242 | 1045 | 39 | 2287 | 8432.80 |

Total: 3 OpenAI calls, 1,666 input + 1,463 output = 3,129 tokens, 62 reasoning tokens included in output, 17,292.24 ms. Zero Gemini generations. Raw responses, snapshot, call ledger and pass are under ignored work/final-validation-2026-10-23. No secrets are included in this report.

Remaining authorization: up to 3 OpenAI calls and 1 Gemini generation for extension PRE + extraction/POST. No repair or automatic retries. devtools.final_validation:app runs on loopback:8000 against the same persistent six-call ledger. The validation pass is capped at six total operations as an extra authorization safeguard; normal operator defaults remain 30 operations/72 hours, six per minute and 200 global calls.

Global cumulative token limit added: PICKYLENS_GLOBAL_TOKEN_BUDGET defaults to 2,000,000. Atomic admission requires both call capacity AND a 300,000-token reservation. Actual reported usage settles the reservation; unknown usage retains it. Serialized provider input/schema and output are bounded. Restart/concurrency/unknown-usage tests pass. 92 Python tests and worker protocol checks pass; whitespace checks pass.

Browser acceptance is waiting for manual extension installation: current Gemini page still displays the old feasibility probe. No production extension review or Gemini generation was attempted. Disable old probe, load extensions/browser, enter the private local validation pass in extension options, and refresh Gemini. No further live authorization is required within the remaining allowance.

VESTA deployment, public checks, deployed extension ZIP and 6-ship remain pending until browser acceptance passes.

## Gemini live acceptance — 2026-10-23

Production candidate loaded in the user Chrome profile after the requested visual refinements. Composer PRE returned Ready. Send original anyway delivered the exact unchanged request. One normal Gemini generation completed. The user-facing explicit Check answer action triggered extraction and POST; all five requirements were Complete. Expanding the recommendation showed an exact excerpt from the correct Gemini response. No automatic POST, retry, regeneration or repair call was made.

Conversation and matching request/answer identifiers are retained only in private local validation evidence. Result panel was directly adjacent to that model-response. Google displayed Gemini Automatic; exact underlying model and token usage were not exposed in the UI and are not inferred.

| Call | Purpose | Model | Effort | Input | Output | Reasoning (included) | Total | ms |
|---|---|---|---|---:|---:|---:|---:|---:|
| 4 | pre | gpt-5.6-sol | low | 376 | 269 | 0 | 645 | 5071.44 |
| 5 | pre | gpt-5.6-sol | low | 376 | 260 | 0 | 636 | 4527.58 |
| 6 | post | gpt-5.6-sol | low | 1219 | 1094 | 49 | 2313 | 11587.85 |

Extension: 3 OpenAI calls, 3,594 tokens, 49 reasoning tokens included, 21,186.87ms. Combined Web+extension: 6 OpenAI calls, 6,723 tokens (3,637 input + 3,086 output), 111 reasoning tokens included, 38,479.11ms. Authorization exhausted; no further inference permitted without approval.

Live backend denial checks: invalid bearer returned 401; exhausted valid pass returned 429 with the allowance message; ledger remained six calls before and after. Credential scan confirmed the actual configured provider key is absent from every extension file. Only the bounded Judge Pass is held by extension trusted storage and sent as authorization.

Options are now exposed both as a normal toolbar popup and an options_ui page; no manual DevTools/storage configuration. Small controls share CSS glasses, subtle hover, visible focus and 5px icon/text spacing. Visual identity rule recorded separately.

Final outstanding acceptance item: user must disable the extension and refresh Gemini so clean host restoration can be inspected. Chrome extension management cannot be automated through the available browser surface. Until this check completes, deployment and 6-ship remain pending. Core Gemini interaction passed; final readiness is conditional on cleanup.


## Acceptance closed and deployment — 2026-10-23

The learner confirmed disabling removes the PickyLens control and reenabling restores it. Gemini browser v0.1 acceptance is complete. Earlier pending statements above describe historical checkpoints.

VESTA now serves https://pickylens.neovantia.live with the existing wildcard certificate, Apache proxy and a dedicated systemd service. Application release: df01953. Protected external runtime configuration and persistent SQLite state are outside the release directory. See deployment/README.md.

External HTTPS checks passed: access/workspace/History 200, invalid pass 401, exhausted pass 429, Secure HttpOnly cookie, no public Replay/test labels. Provider reservations did not increase. No deployed inference was attempted: the authorized six OpenAI calls and one Gemini generation remain the entire final live budget.

The production extension package is work/pickylens-browser-v0.1.zip, pinned to the canonical HTTPS backend. Source extension retains localhost for development. Public shipping is in progress; no video, public repository or Devpost submission has yet been confirmed. Approved planning statuses, completed 5-build and the honest Replay fixture remain unchanged.


## Authorized access correction — 2026-10-23

Public Web now provides automatic anonymous access without a Judge Pass, login or account. Extension APIs alone retain Bearer Judge Pass validation. Anonymous defaults: 12 provider operations per 24-hour session; 6/minute per session and IP; 30/IP/rolling 24 hours. All paths share the persistent 200-call and 2,000,000-token global breakers. Unknown token usage remains reserved. Cookie replacement cannot reset the IP allowance. IP identities are keyed hashes; the proxy trust boundary was verified against spoofed forwarded headers.

Web History is restricted to the current anonymous session; expired/cleared sessions lose access to old records. Prior records and the event trace remain preserved but unowned legacy records are hidden. No account system is introduced. The anonymous cookie is HttpOnly, Secure under HTTPS and SameSite Strict; Web mutations require the same origin. Anonymous tokens cannot authenticate extension routes.

Verification: 97 deterministic tests pass; worker protocol, compilation and whitespace checks pass. VESTA was updated preserving databases, passes and secrets. A fresh browser opened the live workspace directly with Review my request available. Clean HTTPS checks returned 200, blank request validation 422, exhausted anonymous session 429 with the product allowance message, invalid extension pass 401, exhausted extension pass 429. Provider reservation count was unchanged. Zero new inference calls; deployed successful PRE was not rerun because deterministic API tests establish the changed access path and the live provider configuration is unchanged.

This supersedes earlier references to a Web pass gate or shared public History. Existing approved planning status is retained; this is the learner-authorized access amendment. Public repository already existed before this correction; publication was paused until verification passed. 6-ship remains pending video, learner-authored submission, exit survey and submission confirmation.
