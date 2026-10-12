---
doc: spec
status: approved
---

# PickyLens — Technical Spec

## How This Works, In Plain Language

The browser shows the consultant's request and a quiet reviewer. A small Python application serves the pages and handles deliberate user actions. PRE, POST, NEXT, and VERIFY are separate services, independent of HTML, SQLite details, and OpenAI objects.

The first "Review with PickyLens" click creates a saved Interaction. The model proposes requirements and findings, but the user establishes approved intent from the original request, extracted requirements, explicitly accepted clarifications, and final approved prompt. Stable requirement IDs connect evidence across the workflow. POST and VERIFY evaluate the same frozen intent version.

A provider adapter translates requests into OpenAI calls. Environment settings select the model and reasoning effort. Replay replaces only the first answer; all evaluations, follow-up generation, the follow-up call, and verification remain dynamic.

SQLite stores the current snapshot for resume and an append-only event trace for inspection. Every meaningful change saves both atomically. The optional VESTA deployment restricts access at its web server; the application stays single-user without accounts.

This document specifies planned work, not an implemented or tested application. Source: approved scope.md and prd.md.

## The Core Journey Through the System

1. GET / renders the scenario and editable prompt. Opening or editing before PRE creates no History entry.
2. First manual PRE submits a nonblank request and mode. Create the snapshot and interaction_started event, record the attempt, and call PRE through the provider boundary. A failed first PRE remains saved.
3. Validate PRE proposals, assign internal requirement IDs, display findings and human clarification controls, and save explicit user responses. Model suggestions are never implicit acceptance.
4. The user's original/improved prompt choice establishes an approved intent version, including the reviewed extracted requirements and accepted PRE decisions. Confirm Red overrides. Save the final sent prompt verbatim.
5. Acquire the first answer: compatibility-checked real replay fixture or a new live call. Save its provenance and response ID.
6. POST evaluates frozen approved intent and the answer. Validate coverage and evidence; derive four-status counts from the assessments.
7. All Complete ends successfully without NEXT. Needs review alone offers explicit resolution or qualified ending. Partial/Missing enables targeted repair.
8. NEXT generates only permitted repair/approved clarification targets. Save the proposal and edits. User action sends it with the original exchange context and obtains a new response.
9. VERIFY applies the same evaluator to both answers against the same intent. Compare by requirement ID, preserve earlier assessments, and show actual improvement or remaining gaps.
10. History reads snapshots and ordered events. Resume restores only nonterminal work; terminal detail remains read-only.

Implements `prd.md > The Core Journey`, `PRE Review and Approved Intent`, `POST Outcomes Without Repairable Gaps`, and `Minimal Interaction History`.

## Stack

- Existing Python 3.14.3 on Windows; inspected SQLite runtime 3.50.4. Use the existing interpreter, not replacement tooling. [Python SQLite documentation](https://docs.python.org/3.14/library/sqlite3.html).
- FastAPI and Uvicorn for one HTTP application process. [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://uvicorn.dev/).
- Jinja2 server-rendered HTML, vanilla JavaScript fetch actions, and CSS. No SPA or Node asset toolchain. [FastAPI templates](https://fastapi.tiangolo.com/advanced/templates/), [Jinja2](https://jinja.palletsprojects.com/en/stable/).
- Pydantic 2 for provider-neutral contracts, snapshots, events, and structured results. [Pydantic models](https://pydantic.dev/docs/validation/latest/concepts/models/).
- Standard-library sqlite3 with two tables and JSON payloads; no ORM/database server.
- OpenAI Python SDK isolated in its adapter. [SDK](https://developers.openai.com/api/docs/libraries), [Responses reference](https://developers.openai.com/api/reference/python/resources/responses), [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses).
- pytest and HTTPX/FastAPI TestClient for focused tests. [pytest](https://docs.pytest.org/en/stable/), [HTTPX](https://www.python-httpx.org/), [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/).

The application dependencies are not installed in the inspected interpreter. Resolve and pin compatible versions in 5-build; no installation or runtime compatibility test occurred here. Jinja2, Uvicorn, Pydantic, and the testing tools are derived supporting choices for the learner-selected stack, not separately attributed learner decisions.

## Where It Runs and How Someone Tries It

### Local Windows Run and Recording

Project root: C:\__Dev\Neovantia\Apps\PickyLens. During build, use the existing Python interpreter and a suitable project-local virtual environment. Invoke its executable directly; no activation script or PowerShell policy change is needed. Planned requirements.txt/requirements-dev.txt will pin resolved runtime/test dependencies. They are not created in this planning step.

After build and environment setup, from the project root:

    .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

Open http://127.0.0.1:8000/; History is /interactions. Run tests with:

    .\.venv\Scripts\python.exe -m pytest

Supply secrets through the process environment. A future .env.example contains only names and nonsecret defaults. Record compatible Replay Demo, dynamic repair/verification, History evidence, and the Live path. Submission still requires a short demo video and public GitHub repository; deployment is optional and replaces neither.

### Preferred VESTA Deployment

Use the Neovantia-controlled VESTA VPS, one Python application process bound to loopback, and its existing HTTPS reverse proxy. Prefer a dedicated subdomain; a route is acceptable with consistent base-path configuration. Protect pages AND API actions using reverse-proxy HTTP Basic Authentication or equivalent. Credentials remain outside the repository. No product accounts, roles, sessions, or user isolation. One shared History serves the controlled invited audience; no public backend port bypass.

Later authorized deployment steps: inspect OS/runtime/proxy, select hostname/route and port, deploy built application and pinned dependencies, supply an external environment file and durable database path, use existing process supervision, configure HTTPS/proxy access control, test access denial and protected workflow, and document the URL/runbook for 6-ship. Preserve existing services; introduce no Docker, Kubernetes, or cloud services.

VESTA OS, Python, proxy, service manager, hostname, and port are not yet verified. If Nginx is present, use its [Basic Authentication module](https://nginx.org/en/docs/http/ngx_http_auth_basic_module.html); otherwise use the existing equivalent. Resolve these before deployment, not by assuming access or changing the server during specification. Local recording remains sufficient.

A database reset/replacement for demo hygiene is a deliberate manual operation while the app is stopped, never startup behavior or a UI feature. Secrets and databases stay out of Git.

## Look and Feel

Implements `prd.md > Look and Feel` and `scope.md > Inspiration & Identity`.

Warm neutrals, ink/navy text, one cool accent, restrained typography, and compact readable spacing. Derived starting CSS values: background #F5F3EE, surface #FFFEFB, text #17263B, muted #546176, accent #345C92. Use Inter if practical, with Segoe UI/system sans-serif fallback and no essential font download. Monospace only for incidental metadata/evidence.

Green/amber/red convey readiness/status with text labels, never color alone; Needs review is distinct and neutral. Stack the two-column workspace on narrow screens. Use visible keyboard focus and native expandable evidence. No gradients, decorative charts, excessive cards, chatbot styling, or selected mascot/icon. These implement the agreed direction, not an additional design system.

## Components

### Web Application and Workspace

app/main.py assembles dependencies; app/web/ serves Jinja pages and typed action endpoints. Templates show workspace, Interactions list, and read-only detail. Modest workspace.js submits actions and updates the answer/reviewer regions; the server enforces core rules. Escape model text and evidence; never trust generated HTML.

Before first PRE, prompt edits are unsaved workspace data. After creation, save meaningful edits on blur and before navigation/actions; flush pending edits before leaving. A saved indicator requires a committed server acknowledgement. A forced browser/process kill before an edit reaches persistence cannot guarantee keystroke recovery.

Implements `prd.md > Workspace`, `Interactions`, `Empty Requests and Empty History`, and `States and Boundaries`.

### Interaction Coordinator and State Rules

app/services/interactions.py orchestrates core calls and durable transitions; app/core/transitions.py enforces lifecycle, intent version, and supersession. Stage and lifecycle are separate fields. Terminal records cannot mutate/resume.

Request edits return to PRE and require newly approved intent; old results stay superseded in the trace. Mode changes preserve valid PRE/intent, warn before superseding existing response-dependent work, and use the selected mode's response before rerunning POST. No silent reset, mode change, or replay substitution.

Implements `prd.md > Request Changes and Superseded Results`, `Switching Modes During Active Work`, and `Minimal Interaction History`.

### PRE and Intent Establishment

app/core/pre.py proposes material findings, readiness, clarification questions, requirements, and an improved prompt. app/core/intent.py establishes explicit approval and requirement identity. app/prompts/pre.txt provides version-controlled instructions.

Display the proposed requirement representation within the existing reviewer/prompt-approval surface so acceptance is explicit. The existing accept/send choice establishes intent; do not add a separate approval ceremony. Model proposals alone have no approval authority. An edited improved prompt updates its proposed intent for review before sending. Accepted changes link to recorded human decisions; unresolved decisions stay unresolved even after a confirmed Red original-send override.

Approved intent records original request, extracted requirements, explicitly accepted PRE clarifications/constraints/decisions, and final approved prompt. Later evaluation cannot redefine this frozen set.

Implements `prd.md > PRE Review and Approved Intent` and `Request Changes and Superseded Results`.

### POST and VERIFY Evaluation

app/core/evaluation.py exposes one evaluator receiving approved intent, identified answer texts, and phase post/verify. POST supplies the first answer; VERIFY supplies original plus follow-up. app/prompts/evaluate.txt preserves consistent instructions.

Require exactly one assessment for every approved requirement ID, no unknown/duplicate IDs, and valid response references. Store requirement text/status/explanation/evidence/uncertainty. Check cited excerpts occur in the referenced saved answer. Invalid coverage or fabricated references fail validation; insufficient semantic evidence remains Needs review, not unsupported certainty.

Compute counts in application code. Compare before/after by stable requirement ID, not row position or freshly extracted requirements. Partial/Missing are default repair targets. Needs review requires approved additional questioning if existing evidence cannot resolve it. Save revised assessments with their basis while retaining prior events. Structural validation is not proof of semantic correctness.

Implements `prd.md > POST Evidence Review`, `POST Outcomes Without Repairable Gaps`, and `NEXT Follow-Up and VERIFY`.

### NEXT and Follow-Up Execution

app/core/next.py takes approved intent, assessments, answer context, and approved uncertainty targets. app/prompts/next.txt produces minimal follow-up text and targeted requirement IDs. Validate targets against Partial/Missing plus explicitly approved Needs review items.

Generation never sends automatically. Save generated text and edits, then send on explicit user action with the original exchange context. VERIFY uses the same frozen intent afterward. Complete first answers bypass NEXT; uncertainty alone offers resolution or qualified ending.

Implements `prd.md > NEXT Follow-Up and VERIFY` and `POST Outcomes Without Repairable Gaps`.

### Provider Boundary and OpenAI Adapter

app/providers/base.py defines generate_text(messages, purpose) and generate_structured(messages, result_schema, purpose), returning neutral text/typed results and limited request/model/usage metadata. Core services own schemas and rules; no SDK classes, provider continuation IDs, or model literals leak into the core.

app/providers/openai_adapter.py translates these calls and errors. app/config.py reads environment settings. Use the SDK async client for awaited provider calls and repository-owned short-lived SQLite connections; never share a connection across unrelated request threads. The same configured model serves all evaluation stages and, for simplicity, answer calls too. Only OpenAI is implemented now. No plugin framework or second adapter is needed to preserve this boundary.

Implements `prd.md > Replay Demo and Live Model` and the learner's model/host independence constraint.

### Replay Scenario and Compatibility

app/services/replay.py loads app/fixtures/consultant_replay.v1.json. The versioned fixture contains scenario identity/title/description, initial imperfect prompt, canonical approved intent and clarification values, captured first response, and real provenance: provider/model, capture time, exact capture request, and capture ID when available.

Capture/select a genuine response with a material quality defect during build. Never fabricate capture provenance or instruct the model to fail deliberately. Bind the fixture to canonical structured approved intent and scenario constraints. Map fixture-local canonical requirement keys to interaction requirement IDs. Check compatibility deterministically by comparing the approved requirements, accepted clarifications, constraints, and decisions using canonical scenario keys and typed values. Superficial wording changes remain compatible when that structured intent is unchanged; presentation text, literal prompt equality, and interaction-local IDs are not compatibility criteria. Do not use rigid text matching, fuzzy semantic guesses, or a separate model-based equivalence call. If canonical mapping cannot be established deterministically, or any substantive intent/constraint differs, block Replay and offer "Reset to the canonical demo scenario" or "Continue in Live Model". Never alter approved intent to make a fixture fit. The compatibility check itself makes no AI call.

Only first-answer acquisition is replayed. Other stages use the same live evaluation pipeline. Incompatibility offers explicit reset or Live; attempted Live-to-Replay switching may remain Live. Reset preserves prior trace and explicitly reestablishes canonical scenario/intent.

Implements `prd.md > Replay Demo and Live Model` and `Switching Modes During Active Work`.

### SQLite Repository and History

app/storage/ handles two tables, typed JSON payloads, and explicit transactions. Resume uses the canonical snapshot; list uses title/time/mode/status; detail inspects ordered events and superseded evidence.

For each meaningful transition: validate payload, begin one write transaction, check expected revision, append ordered event, update snapshot, commit. Roll back both on failure. Never hold a write transaction across a model call. No event update/delete operations are exposed; database triggers reject historical event updates/deletion as an append-only guard.

Implements `prd.md > Minimal Interaction History` and the accepted persistence design.

## Data Model

### Tables and Identifiers

interactions: interaction_id TEXT PRIMARY KEY (UUID4), schema_version INTEGER, title TEXT, mode TEXT, stage TEXT, lifecycle_status TEXT, current_intent_version INTEGER nullable, revision INTEGER, last_event_sequence INTEGER, created_at TEXT, updated_at TEXT, snapshot_json TEXT.

interaction_events: event_id TEXT PRIMARY KEY (UUID4), interaction_id TEXT referencing interactions, event_type TEXT, sequence_number INTEGER, timestamp TEXT, operation_id TEXT nullable, approved_intent_version INTEGER nullable, payload_schema_version INTEGER, payload_json TEXT. All fields except operation_id and related intent version are required. Enforce UNIQUE(interaction_id, sequence_number), foreign keys, and valid JSON payload/snapshot text. Add a unique index on operation_id WHERE operation_id IS NOT NULL; idempotency uses this relational column, not a JSON payload index. Use UTC ISO-8601 timestamps; sequence numbers establish per-interaction order. Display timestamps in the browser's local timezone.

No additional relational tables. Index snapshot updated_at for list order and event interaction_id/sequence_number for trace reads. Use parameterized SQL and connection-scoped explicit transaction control consistent with Python 3.14. [Transaction documentation](https://docs.python.org/3.14/library/sqlite3.html#transaction-control).

### Typed Payloads and Intent Versions

InteractionSnapshot: schema_version, request_revision, original/current request, selected prompt, mode, stage, lifecycle_status, title/timestamps, current PRE proposal, accepted clarifications, current approved intent, response IDs/text, POST assessments, NEXT proposal/edited draft, follow-up response, VERIFY result, operation/failure/recovery data. Current pointers refer only to canonical results; superseded payloads remain in events.

ApprovedIntentVersion: version, request_revision, original request reference/text, final approved prompt, approved_at, explicit approval/override action, accepted clarification/constraint/decision records and provenance, requirements. Requirement: requirement_id, text, source references. Preserve IDs across stages. Across a new intent version, retain an ID only for the same explicitly preserved requirement; new/materially changed requirements receive new IDs. Do not let a model silently remap semantics.

RequirementAssessment: requirement_id, requirement_text, status (complete/partial/missing/needs_review), explanation, evidence[] (response_id, excerpt, location), uncertainty_reason nullable. Optional qualitative confidence is self-reported, not calibrated probability or proof. EvaluationResult: intent_version, phase, assessments, derived summary. Check IDs/text against frozen intent outside provider schema validation.

PREProposal, ClarificationAcceptance, NextProposal, ModelAnswer, OperationAttempt, FailureRecord, and typed event payloads live in app/core/contracts.py. Event envelopes include the nullable operation_id column metadata above and an event_type-discriminated payload schema. User/API operation claim events require a non-null operation_id; related stage-result events refer to that claim through validated payloads. Reject invalid data before persistence. OpenAI JSON Schemas use its supported strict subset, with explicit nullable fields.

Representative event types: interaction_started, request_changed, stage_started, pre_completed, clarification_accepted, intent_approved, mode_changed, response_received, post_completed, uncertainty_resolved, next_generated, followup_edited, followup_sent, verify_completed, stage_failed, interaction_paused, interaction_completed, interaction_resumed. Supersession is a new transition recording affected versions/results, never a mutation of old events.

### Operations, Restart, and Stale Responses

Action requests carry operation_id and expected_revision. Claim each user/API operation once through an append-only event with its operation_id in the nullable relational column. The unique index for non-null operation IDs prevents duplicate claims directly at the database level, including concurrent first PRE creation; no third table or JSON idempotency index is needed. Check for an existing operation claim before applying expected_revision validation: a completed duplicate returns its stored outcome, and an in-progress duplicate returns its current pending state without another call or event. New obsolete/conflicting actions still return 409 and current saved state. Stage-specific details remain in validated JSON. When one operation produces multiple trace events, only the claim event has the non-null operation_id; later result/failure events keep operation_id null and reference the claim event/operation in their typed payloads. This preserves global operation-ID uniqueness without suppressing the append-only stage trace. Claiming an operation, appending its event, and updating the snapshot remain atomic in one SQLite transaction.

Commit stage_started before a provider call. Perform the call outside the write transaction; validate and atomically save its outcome afterward only if the operation/version is still current. A late response from superseded work stays traceable but cannot become a current finding.

On process startup, previously unfinished operations become interrupted/retryable, never successful or automatically retried. Preserve last completed context. A remote answer lost before durable saving cannot be guaranteed recovered; explicit retry may incur another call. No background queue, branching UI, or automatic workflow restart.

## HTTP Contracts

Mutations use JSON and server-validated actions, with operation_id and expected_revision after creation. Results return interaction_id, revision, stage, lifecycle_status, a current-state view, and concise errors/next actions. No credentials enter browser payloads.

- GET /: unsaved initial workspace. GET /interactions: list. GET /interactions/{id}: read-only detail. GET /?interaction={id}: restored nonterminal workspace.
- POST /api/interactions/pre: first manual PRE creates an Interaction. Payload request_text, mode, operation_id. Whitespace receives 422 with no record. Persist creation/attempt before calling PRE so failure retains the Interaction.
- POST /api/interactions/{id}/request: save changed request, supersede dependent results, return to PRE. POST /api/interactions/{id}/pre: deliberate rerun for current request.
- POST /api/interactions/{id}/clarifications: save explicit user answers and update the proposal without auto-approval. POST /api/interactions/{id}/approve-intent: save reviewed requirement set, accepted decisions, selected final prompt, and confirmed Red override when applicable.
- POST /api/interactions/{id}/answer: acquire compatible replay or live first answer. POST /api/interactions/{id}/post: evaluate it.
- POST /api/interactions/{id}/uncertainty: resolve/retain a Needs review item; additional AI-question targeting requires explicit approval.
- POST /api/interactions/{id}/next: generate permitted minimal follow-up. POST /api/interactions/{id}/followup-draft: save edits. POST /api/interactions/{id}/followup: explicitly send and save the new model response. POST /api/interactions/{id}/verify: evaluate combined answers.
- POST /api/interactions/{id}/mode: switch after required warning/confirmation; preserve valid intent and supersede response-dependent current results. It does not silently call a model before the explicit AI action.
- POST /api/interactions/{id}/reset-scenario: deliberate canonical reset with old trace retained. POST /api/interactions/{id}/finish: finalize only supported complete/qualified outcomes or stop/pause incomplete. POST /api/interactions/{id}/resume: restore nonterminal work.
- GET /api/interactions/{id}: current read-only view. Retry uses the failed stage's endpoint and a new operation_id. No arbitrary state-writing, delete/export, accounts, or settings endpoints.

400/422: invalid action/input; 404: unknown interaction; 409: stale/conflicting/terminal mutation; 502/504: provider/timeout failure with prior context preserved. Storage failure never returns saved success. The UI may chain a completed follow-up call into VERIFY while saving both stages; generation and sending remain user-controlled.

## File Structure

Planned files only; no implementation is created in 4-spec. Package directories include __init__.py.

    PickyLens/
    ├── app/
    │   ├── main.py                      # FastAPI assembly/startup recovery
    │   ├── config.py                    # Environment configuration
    │   ├── core/
    │   │   ├── contracts.py             # Domain schemas, snapshots, events
    │   │   ├── transitions.py           # Lifecycle/version/supersession rules
    │   │   ├── intent.py                # Human approval, stable requirement IDs
    │   │   ├── pre.py                   # Material request review
    │   │   ├── evaluation.py            # Shared POST/VERIFY and evidence checks
    │   │   └── next.py                  # Minimal follow-up targets/text
    │   ├── providers/
    │   │   ├── base.py                  # Neutral provider protocol/results
    │   │   └── openai_adapter.py        # Responses API translation/errors
    │   ├── services/
    │   │   ├── interactions.py          # Orchestration/durable transitions
    │   │   └── replay.py                # Fixture/provenance/compatibility
    │   ├── storage/
    │   │   ├── sqlite.py                # Connections/schema initialization
    │   │   ├── repository.py            # Atomic snapshot/event writes
    │   │   └── schema.sql               # Two tables/indexes/append-only guards
    │   ├── web/
    │   │   ├── routes.py                # HTML page routes
    │   │   ├── api.py                   # Explicit typed action endpoints
    │   │   └── viewmodels.py            # Safe UI views/derived counts
    │   ├── templates/
    │   │   ├── base.html
    │   │   ├── workspace.html
    │   │   ├── interactions.html
    │   │   └── interaction_detail.html
    │   ├── static/
    │   │   ├── styles.css
    │   │   └── workspace.js             # Modest fetch/rendering, no core rules
    │   ├── prompts/
    │   │   ├── pre.txt
    │   │   ├── evaluate.txt
    │   │   └── next.txt
    │   └── fixtures/
    │       └── consultant_replay.v1.json # Genuine captured response/provenance
    ├── tests/
    │   ├── test_intent_and_transitions.py
    │   ├── test_evaluation_contracts.py
    │   ├── test_repository_atomicity.py
    │   ├── test_replay_compatibility.py
    │   └── test_workflow_routes.py
    ├── data/                            # Ignored SQLite database/journals
    ├── work/                            # Ignored scratch when needed
    ├── devpost/                         # Skill Pack docs/companions
    ├── requirements.txt                 # Pinned compatible runtime dependencies
    ├── requirements-dev.txt             # Pinned compatible test dependencies
    ├── .env.example                     # Secret-free names/defaults
    ├── .gitignore                       # Preserve rules; ignore runtime files
    └── README.md                        # Setup/recording/fixture provenance

Preserve .git, .agents/skills, and current work. Leave legacy .claude links alone. No tooling reinstallation, PowerShell policy changes, or Node/npm/npx use is required.

## External Services and Dependencies

### OpenAI Configuration and Calls

Planned environment configuration:

    OPENAI_API_KEY=<supplied outside source control>
    PICKYLENS_PROVIDER=openai
    PICKYLENS_MODEL=gpt-5.6-sol
    PICKYLENS_REASONING_EFFORT=low
    PICKYLENS_DB_PATH=data/pickylens.sqlite3
    PICKYLENS_API_TIMEOUT_SECONDS=120

These are configuration defaults, not core literals. Validate at startup; do not silently substitute models. The selected model serves all evaluation stages and answer calls unless a later explicit decision changes this.

Use POST https://api.openai.com/v1/responses with Bearer API-key authentication. Adapter structured calls use responses.parse and a Pydantic result schema: configured model, reasoning={effort: configured effort}, input messages, store=false, and strict JSON Schema output formatting. Map output_parsed to neutral domain results. Answer calls use responses.create and output_text. Handle refusal, incomplete output, invalid structures, and empty text explicitly. [Responses](https://developers.openai.com/api/reference/python/resources/responses), [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses).

Send explicit local context rather than depending on provider-held conversations. No tools/web search/hosted agents/provider storage. Use a bounded timeout and disable SDK automatic retries; recovery remains explicit. Keep keys server-side and log only relevant request/model/usage metadata. Schema validity does not establish judgment correctness.

The official [gpt-5.6-sol page](https://developers.openai.com/api/docs/models/gpt-5.6-sol) confirms low effort and Structured Outputs. Published standard text pricing at research time: $4 per million input tokens, $20 per million output tokens; effective charges depend on usage and applicable conditions. No fixed interaction cost is asserted. Account access, rate limits, and remaining budget are unverified; check the selected model with a real call early in build. Handle 429 without unbounded retry. Lower-cost models remain deferred.

### SQLite and VESTA

SQLite is embedded local storage. Ignore runtime databases/journals/WAL/SHM files, virtual environments, private scratch, secrets, and credential files. Preserve existing .gitignore rules when adding exclusions during build; no live database is committed as a replay fixture.

VESTA uses existing Neovantia hosting and HTTPS proxy; no new account/infrastructure cost is assumed. Confirm server resources, operating arrangements, and access control before deployment. Public source/video remain separate from the protected demo.

## Important Failure Modes

- Provider refusal, timeout, rate limit, or invalid assessment: persist failed attempt/stage, retain completed context, show a concise retry/edit/stop choice. Never fabricate fallback evaluations or successful completion.
- SQLite write failure or process interruption: roll back snapshot/event together, do not claim saved success, preserve browser context where possible. Startup exposes interrupted work as retryable, never silently repeats billed calls.
- Replay mismatch or invalid fixture: block replay and offer reset/Live. If a genuine suitable fixture is unavailable, say so rather than inventing one.

Implements `prd.md > States and Boundaries`. Editing after a failure follows intent-version supersession rules rather than reusing stale reviews.

## Verification Approach

Use temporary SQLite files and a clearly test-only provider stub for deterministic checks; stubs are not runtime demo modes. Derive tests from PRD behavior, not implementation mirroring.

- Persistence: atomic rollback, ordered unique events, append-only guards, typed payload rejection, reopen/restore.
- Transitions: no History before first PRE, deduplicated creation, explicit intent/Red override, terminal immutability, and different invalidation for edits versus mode changes.
- Evaluation: frozen requirement coverage, four-status counts, real excerpt references, Needs review handling, permitted follow-up targets, and no unnecessary NEXT.
- Routes: workspace/empty History, nonterminal Resume, replay mismatch choices, graceful failure, retry preservation, saved edits.
- Browser: compact/narrow layout, clarification controls, inspectable evidence, conditional repair, before/after status changes, and terminal History without Resume.
- Real API checks: exact model/low effort/schema support, actual PRE/POST/NEXT/VERIFY, Live answers, and manual evidence review. Verify the captured material defect is genuine; do not require fixed counts across live runs.
- Deployment: HTTPS/proxy protection for pages and API, no public backend bypass, restart persistence, and local independence.

Run focused tests as their implementation slices exist; broaden only for changes/failures. No application code, tests, API calls, or deployment are executed during this planning step.

## What Was Simplified and Why

Two tables with validated JSON replace a normalized stage database. Jinja/vanilla JavaScript replace an SPA/toolchain. One provider/model replaces configuration UI. Foreground explicit actions replace queues/background retries. Proxy protection replaces application accounts. A genuine captured first answer makes the demonstration repeatable without faking the kernel.

The complete quality loop and minimal History remain intact. No Smart/Always modes, host adapters, export/search/history editing, or commercial features are added.

## Decisions and Open Issues

### Agreed Consequential Decisions

Learner-selected: Python/FastAPI, server-rendered lightweight frontend, SQLite, JSON replay, OpenAI abstraction, gpt-5.6-sol/low via environment, local Windows execution, protected VESTA preference, versioned user-authoritative intent, stable requirement IDs, and atomic snapshot-plus-append-only-event trace. Accepted tradeoff: typed JSON instead of extensive relational normalization.

Derived details proposed for review: Jinja2/Uvicorn/Pydantic, UUID4 IDs, sequence ordering, explicit endpoints, optimistic revisions, schema/prompt files, and annotated tree. These are not claims the learner individually chose every implementation detail.

### Learning Topic: Core Independence and Evidence

The learner wants to understand model/host independence. The concrete boundary explained during specification is that core services/schemas own intent, IDs, evidence, and transitions; a provider adapter only translates calls/results. A future host adapter can use the same core without the web UI or OpenAI SDK. No future adapter is implemented now.

The learner explicitly distinguished structural schema validity from semantic correctness. Evidence checks and manual semantic smoke review preserve that distinction. Build evidence will include core tests through the neutral provider protocol and an independent adapter smoke check. These are discussed principles, not demonstrated implementation mastery.

### Build and Ship Checks

- Verify/pin compatible packages for the existing interpreter; no tooling replacement is assumed.
- Confirm actual account/key access and schema behavior with the exact chosen model. Do not switch models silently if access fails.
- Capture/select a genuine response with a material quality defect and document exact canonical intent/provenance. Scenario sample content and capture evidence are not invented in this spec.
- Inspect VESTA OS/proxy/Python/process supervision/port/domain and external credential provisioning before deployment; local recording remains sufficient.

No unresolved product choice is assumed. This technical specification is approved. Do not start implementation or 5-build without explicit approval.


## Authorized Replay Quality-Defect Amendment

Replay requires a genuine, unmanipulated response containing at least one material quality defect that PickyLens can identify and demonstrate meaningfully, such as an omission, contradiction, inconsistency, or unresolved uncertainty. Preserve the response exactly as captured and retain provenance. Never insert or manufacture a defect or hardcode an expected Replay assessment. Partial means addressed but materially inconsistent or unreliable; Needs review means evidence is insufficient to establish whether an apparent inconsistency is real.


### Slice 3 Implementation Mapping

Slice 3 implementation route mapping: /retry and the failed stage endpoint support explicit retries; /pause and /resume preserve nonterminal work; /resolve reassesses existing uncertainty evidence; /approve-uncertainty authorizes targeted question generation; /finish-review records the qualified terminal outcome. These concrete action names implement the recovery and uncertainty contracts above without changing product behavior. Run one application process per SQLite instance for startup interruption recovery.


### Authorized Workbench Presentation Refinement

Final-review presentation refinement: an approximately equal-width request/answer workbench replaces the reviewer sidebar. Native DOM order is request/review, answer/check, follow-up prompt, follow-up answer/verification; CSS places request content left and response content right on desktop and stacks it on narrow screens. Focus/scroll cues move to newly received answers without a read-confirmation gate. Human-language actions map to unchanged internal stages and endpoints. Core semantics, persistence, recovery, provider behavior, and Replay provenance remain unchanged.

## Authorized New-Case and Active-Case Orientation

New cases retain the full introduction, first-use guide, human-language process, and two-sided workbench headings until Review my request begins. Active cases collapse introductory decoration and retain a compact sticky header/navigation/mode control, process progress with current/completed/future states, and request/answer orientation links. Narrow screens use shorter orientation labels and hide secondary methodology abbreviations. Starting a new case automatically restores the full introduction. This is presentation derived from interaction state, with no preference, persistence, provider, or recovery change.
