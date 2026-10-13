# Browser robustness follow-up — 2026-10-13

Decision: NO-GO for building the full extension from this probe. This is an implementation/lifecycle validation failure, not proof that Gemini web integration is impossible. Production Core remains untouched.

## Observed results
- Composer injection and normal typing worked after reloading the manifest and refreshing the page.
- Enter and mouse Send interception worked. Explicit Send original anyway delivered unchanged requests.
- Two agent-submitted consecutive turns completed in the same conversation. The user also submitted one turn while the extension was disabled; conservatively the three-generation budget is exhausted. Zero OpenAI calls.
- New turn container IDs paired each request with its response. However, neither newly completed answer received a POST marker. Holding generating state across intermediate mutations passed a unit test but did not correct the browser failure. The actual transition signal needed for reliable completion remains unverified.
- Regeneration and interruption were not exercised in the browser. Exactly-once POST across completion, regeneration and refresh is NOT established. In-memory state is lost on refresh; absence of duplicate panels is not evidence of correct restoration.
- An invalidated extension context threw synchronously during review after an extension reload; refreshing the Gemini tab restored interception. This failure path still needs a graceful implementation before product use.
- Native controls use observed icon identifiers arrow_upward (Send), stop, refresh and copy. The adapter isolates these plus contenteditable role=textbox, model-response, user-query, turn IDs and aria-busy. No localized button labels are used by the adapter. These remain undocumented host dependencies; there is no verified alternate completion signal.

## Backend gate
The real browser displayed the deterministic local mock result through content script -> service worker -> http://127.0.0.1:8033/probe/review -> validated response -> content script. No production Core or provider is connected.

Permissions: content scripts only https://gemini.google.com/*; host_permissions http://127.0.0.1/* (Chrome patterns do not constrain port). Worker fixes endpoint/port/path and checks sender ID, sender URL, type and text length. Mock validates JSON shape and length; worker validates response kind/message and applies a two-second timeout. No API keys or credentials in extension or browser storage. Background host permission enabled the observed request without backend CORS headers; this does not confer server authentication. Future protected service access needs server-side authentication and authorization, with provider secrets server-side only.

Gate E: round-trip mechanics PASS; timeout/malformed-response browser checks not completed. Code paths alone are not browser verification.
Gate C: FAIL in current probe. A/B basic mechanics PASS. D prior static placement was proven, but automatic placement for newly completed answers FAILS here.

## Verification and stop
Seven lifecycle assertions pass, including intermediate-state retention and aborted-state classification. They test a pure classifier, not Gemini transitions. JavaScript syntax and Git whitespace checks pass. No full-extension build, production integration, additional inference or 6-ship authorized by this record.

The extension remains enabled at reporting time. User must disable it in Chrome extension management and refresh Gemini; automated extension-management access is unavailable. Prior feasibility evidence remains in RESULTS.md and commit 84c966f.
