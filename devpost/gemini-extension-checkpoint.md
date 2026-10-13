---
doc: gemini-extension-checkpoint
status: deterministic-complete
baseline: aeb5c6a
---

# Gemini CLI v0.1 deterministic checkpoint

2026-10-13. The approved Live Web milestone and completed 5-build remain closed. No live OpenAI or Gemini inference calls were made. No tools were installed or reinstalled, and PowerShell execution policy was not changed.

## Implementation

Two extension command hooks call a transport-only Node launcher and a Gemini-specific Python adapter. Shared host-neutral orchestration calls the existing PRE/evaluation/NEXT functions, typed contracts, provider abstraction, operation-local telemetry and transactional snapshot/event repository. Gemini generates the answer; no Gemini client/provider is added to core. The original submitted request remains canonical and extraction is explicitly not represented as user-confirmed. Suggestions are never accepted automatically.

Host records use `data/gemini.sqlite3`, not the web database. Hook reservations preserve validated payloads and protect against duplicate or ambiguous matching. Completed work, failed calls and late superseded results remain traceable. Hook output is restricted to advisory `decision: allow` and `systemMessage`; no denial, context injection or automatic retry. Manual repair requires explicit invocation and never submits to Gemini. No host-native inference experiment or commercial optimization was implemented.

## Installed interface verification

- Existing executable: `C:\Users\alons\AppData\Roaming\npm\gemini.cmd`.
- Package and `--version`: 0.63.0.
- Normal profile initially reported no installed extensions. It was left unchanged.
- Actual installed bundle inspected: `bundle/chunk-RWBXO4OP.js`, imported by the installed entry point. Confirmed base fields, BeforeAgent/AfterAgent payloads, extension registration, synchronous execution, advisory messages and retry semantics.
- The extension was linked and enabled using the actual CLI with an isolated `GEMINI_CLI_HOME` under `work/gemini-063-profile`.
- Actual HookRegistry registered exactly `BeforeAgent: pickylens-request-review` and `AfterAgent: pickylens-answer-review`, source `extensions`.
- Actual HookRunner executed both configured launcher commands successfully, exit 0 and advisory output. Credentials and local `.env` loading were explicitly disabled for this transport probe; it verified the failure path without inference. Successful and defective assessment paths use deterministic providers in tests. Interactive message appearance during a real Gemini turn remains part of live hands-on validation.

No material interface mismatch requiring product changes was found. The CLI exposes no stable turn ID: ambiguous/overlapping turns fail safely to manual review. Environment sanitization means arbitrary parent variables are not a reliable secret transport; project-local `.env` remains the supported local development path.

## Verification evidence

- Full automated suite: **83 passed** (54 existing and 29 new adapter tests).
- Python compilation and Node syntax checks pass.
- Tests cover four assessment states, unchanged intent, evidence, complete-answer stopping, manual review/show/repair, explicit uncertainty approval, duplicate/concurrent delivery, sequential identical requests, separate sessions, unmatched and stale hooks, interrupted reservations, failures, timeouts, empty answers and trace-only superseded results.
- The real HookRunner transport probe can be repeated without inference using `node devtools/gemini_protocol_probe.mjs INSTALLED_CORE_BUNDLE_PATH`. It is a version-specific development check, not a runtime dependency on Gemini internals.
- Replay fixture SHA256 remains `75dcd41aea1591ccce90e5dff4307b6680a974bdb9872e56f6374aea297794e3`.
- Approved scope, PRD, spec, checklist, historical app map and previous live evidence remain unchanged.

## Enablement and remaining limitations

Exact PowerShell setup and technical fallback commands are in `extensions/pickylens/README.md`. Normal-profile enablement is deferred until the live budget is approved, to avoid accidental review calls. No Google credentials were copied into the isolated profile.

This is a repository-linked local extension, not a packaged distribution. It evaluates self-contained text and final answers, not tool side effects or implicit multi-turn context. A hard-killed hook may leave pending state and unknown usage; an explicit file-based manual review creates a new record. An overlapping/interrupted host session requires explicit manual inputs or a fresh session. No automatic host retry or repair-chain association is implemented. Manual shell passthrough is a technical fallback only; native/judge-facing manual UX is deferred.

## Proposed bounded live validation — not authorized yet

Expected application work: **one Gemini task turn, one OpenAI PRE call and one OpenAI POST call**. Expected inference requests for a simple tool-free task: **1 Gemini + 2 OpenAI = 3**. No NEXT, repair, second Gemini task, capture retry or provider experiment is included. A failure or unexpected need stops validation.

The extension cannot guarantee Gemini's internal API-request count: the host may perform auxiliary inference or retries outside these hooks. Inspect Gemini's reported usage and distinguish its task turn from observed provider requests; do not claim a strict all-in Gemini API ceiling from hook telemetry. If approval requires that strict ceiling, resolve host-level controls before running. The OpenAI adapter disables SDK retries, and PickyLens will issue at most the two planned review calls.

Stop here for approval of the live budget. Do not begin 6-ship.
