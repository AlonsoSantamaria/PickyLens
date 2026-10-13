# PickyLens Gemini CLI extension v0.1

Experimental adapter for Gemini CLI 0.63.0. Gemini writes the answer; the existing PickyLens OpenAI provider reviews the request and answer. The web application is unchanged. No host-native inference adapter is included.

## Local setup and enablement

Use the existing Gemini installation and the existing PickyLens Python environment. Keep this extension linked to the repository: its launcher resolves `.venv` and the application relative to its own location. It is not a standalone distributed package.

After the live validation budget is approved, run in PowerShell:

```powershell
Set-Location C:\__Dev\Neovantia\Apps\PickyLens
& 'C:\Users\alons\AppData\Roaming\npm\gemini.cmd' extensions link 'C:\__Dev\Neovantia\Apps\PickyLens\extensions\pickylens'
& 'C:\Users\alons\AppData\Roaming\npm\gemini.cmd' extensions list
```

Read and accept the CLI's extension confirmation. Start a fresh Gemini session using the same executable. Check `/hooks` lists `pickylens-request-review` for BeforeAgent and `pickylens-answer-review` for AfterAgent. `/hooks enable-all` enables hooks if globally disabled; do not use it indiscriminately if other hooks are intentionally disabled. The isolated deterministic profile is under `work/gemini-063-profile`; do not use that profile for your normal Google session.

Local review configuration loads the project's ignored `.env`, with environment variables reaching the Python process taking precedence. Gemini sanitizes subprocess environments; do not assume an external secret environment variable is forwarded. The already configured project-local `.env` is the supported development path. No secret belongs in the extension manifest or hook command. The existing VESTA external service environment plan remains unchanged; this local extension does not deploy a service.

Records default to `data/gemini.sqlite3`, separate from web History. `PICKYLENS_GEMINI_DB_PATH` can override it when passed to the adapter process. The adapter never reads Gemini OAuth tokens or transcript contents. It saves the hook-supplied request, answer, review findings and correlation metadata locally.

## What the user sees

Before the answer: `PickyLens | Review request`, readiness and concise findings, then a reminder that the unchanged request continues. Suggested clarification answers are never accepted automatically.

After the answer: `PickyLens | Check answer`, four-state counts, defects or uncertainty with evidence, and the next useful action. Complete answers end with `The answer meets the reviewed requirements. No follow-up needed.` Missing/Partial items offer a manual repair draft; Needs review stays uncertain. No repair is automatically generated, submitted or claimed verified.

These are assessments of the explicit request and final textual answer, not proof of tool side effects or implicit conversation context. Extracted requirements remain model interpretations. The submitted request remains authoritative.

## Technical manual fallback

This is not the approved final judge-facing or commercial manual UX. Native manual invocation is a deferred UX task.

From the repository, read an existing report with zero model calls:

```powershell
.\.venv\Scripts\python.exe -m app.adapters.gemini show --interaction RECORD_ID
```

Inside Gemini, prefix the same command with `!`. Use the exact record ID shown by the hook; no implicit latest-session selection is performed.

Explicitly request a fresh review of UTF-8 files:

```powershell
.\.venv\Scripts\python.exe -m app.adapters.gemini review --request-file work/request.txt --answer-file work/answer.txt
```

This creates a separate saved review and normally makes two OpenAI calls. Omit `--answer-file` for manual preflight (one review call, no Gemini task). This is also the technical recovery path after an interrupted/ambiguous host turn. It does not modify the old record or resubmit to Gemini.

Generate a targeted draft only when desired:

```powershell
.\.venv\Scripts\python.exe -m app.adapters.gemini draft-repair --interaction RECORD_ID
```

This makes at most one OpenAI call and does not send anything to Gemini. Complete records have no repair targets. Needs review items are excluded unless explicitly selected with `--approve-uncertainty REQUIREMENT_ID`. `show` exposes stable requirement IDs and full evidence. Existing drafts are returned without another call.

## Boundaries and failures

Exactly two command hooks are declared, each with a 55-second host timeout. Review execution is bounded at 45 seconds, the child launcher at 50 seconds. Failures yield advisory messages and preserved records, never denial or retry. A hard process termination can leave a pending operation with unknown usage; inspect it or perform manual review. There is no background recovery or automatic retry.

Gemini 0.63.0 supplies session metadata and timestamps but no unique turn ID. Sequential turns and exact duplicate deliveries are supported. Overlapping/incomplete turns in one session are conservatively quarantined from automatic matching; use explicit manual inputs or a new Gemini session. Historical hook payloads are retained even when correlation fails. Different sessions remain independent. No generic multi-turn repair association is claimed.

The Google session produces the answer. Two OpenAI review calls are expected for a normal supported turn. Gemini internal/auxiliary inference is not counted by these hooks; do not mistake PickyLens review telemetry for total Gemini usage. Live validation remains separately gated.
