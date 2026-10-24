# PickyLens

Quality-check the whole AI interaction.

Live demo: https://pickylens.neovantia.live/ (no account, login or code required).

Source: https://github.com/AlonsoSantamaria/PickyLens · MIT License.

The Web app provides request review, answer checking, targeted follow-up and verification with saved History. The optional Gemini Chat extension provides request review and explicit answer checking alongside normal Gemini conversations. Provider credentials stay on the server.

Download the production extension ZIP from [GitHub Releases](https://github.com/AlonsoSantamaria/PickyLens/releases/latest), then follow [installation instructions](extensions/browser/README.md). Do not load the localhost development source for the public service.

## Run PickyLens locally

The normal public/judge-facing application uses live AI through the configured OpenAI adapter, with no Replay selector or synthetic fallback. From the project directory, run:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Set `OPENAI_API_KEY` locally outside source control. Open http://127.0.0.1:8000/. Review the consultant scenario, choose the request you approve, send it, read the answer on the right, and choose Check this answer. A fully complete first answer ends successfully. Repair is offered only for genuine gaps; uncertainty remains Needs review and requires the existing explicit approval path. Opening the workspace makes no model calls. Missing live configuration is reported clearly without substituting Replay or a stub.

The normal API rejects internal Replay operations and keeps pre-existing internal records out of the public workspace/History while preserving them in storage. This is product separation, not authentication or multi-user isolation. Use separate databases for internal and controlled public instances.

## Internal Replay diagnostics

The engineering-only runner is `devtools.replay_app:app`. Start it locally on a separate port with `PICKYLENS_DB_PATH` pointing to an internal database. Do not expose it as the public application. It retains the Replay/Live selector, canonical binding, genuine captured contradiction, and provenance/integrity checks. Replay replaces only first-answer acquisition; reviews and follow-up remain model-backed. The historical Slice 2 evidence remains in `devpost/live-verification.md`.

The fixture is unchanged. It contains conflicting cost statements; no expected assessment is embedded. Dynamic judgments can vary. Internal mode switches preserve superseded evidence and require confirmation; conservative structured compatibility remains enforced.

## Try the flow without model calls

The separate development runner uses real SQLite persistence and a **clearly labeled deterministic development stub** for all AI behavior. Stub outputs and evaluations are synthetic and scenario-specific, not real model evidence or a captured Replay Demo. No API key is needed and no live calls are made.

From PowerShell in the cloned repository:

```powershell
.\.venv\Scripts\python.exe -m uvicorn devtools.stub_app:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/. Use the prefilled consultant scenario. Review, select **Lowest upfront cost**, save the clarification, choose Use improved request, send the request, read the first response on the right, and choose Check this answer. Generate a targeted follow-up, optionally edit/save it, explicitly send it, and verify both responses. Open Interactions and inspect the saved evidence and ordered trace. Restarting the server retains saved work in `data/slice1-stub.sqlite3`.

The stub is deliberately narrow. Editing the request does not make its synthetic semantic behavior general-purpose. The banner and stored metadata distinguish these records from live/replay interactions. Recovery and request revision use the same coordinator as the real application.

The real application assembly is `app.main:app`. The development stub is injected by `devtools.stub_app`, not selectable through a product setting.

## First-time setup (skip when .venv already exists)

Use an existing Python 3.12 or newer installation. Run these commands from your clone; the deployed service uses Python 3.12.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

No activation script, execution-policy change, Node tooling, or system runtime replacement is required.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Tests use temporary SQLite databases and the injected deterministic provider. Credentials, virtual environments, runtime databases, private learner context, and scratch data are ignored by Git. No deployment or submission work is included in this slice.

## Runtime configuration

Development loads only the project-root `.env`, with normal process environment variables taking precedence. Secrets are masked in configuration representations and never included in browser responses. `.env.example` contains names and safe defaults only. No implicit search in parent directories is performed.

For VESTA, set `PICKYLENS_ENV=production` in the service environment to disable repository dotenv loading. Plan to use systemd `EnvironmentFile=/etc/neovantia/secrets/pickylens/runtime.env` with the same variable names and restrictive permissions. Do not place deployment secrets in the checkout. The original reverse-proxy-only access plan is superseded by the authorized Judge Pass finalization below. Keep the backend behind the trusted HTTPS proxy; Judge Pass protects Web and extension evaluation. Deployment is now active; see deployment/README.md for the installed service and verification.

The bounded Slice 2 verification harness is `python -m devtools.live_verify`; it records attempts and usage under ignored `work/live-verification/`, disables SDK retries, and refuses automatic reruns of an existing capture. Never run it without an authorized live-call budget.


## Recovery and boundaries

Run one application process/worker per SQLite instance. On startup, unfinished operations become interrupted and require an explicit retry. Completed context is preserved; there are no automatic model retries. If a remote answer was lost before saving, retry can incur another model call.

Every mutation has an operation ID and expected revision. Re-delivery of the same operation returns its saved outcome or pending state without another call. Reusing an ID for different input is rejected. Stale clients receive HTTP 409 and the current snapshot. Provider failures return a concise 502/504 message and the saved snapshot. Failure never advances the stage.

In the workspace, Pause preserves work; Resume restores it. Retry runs only the failed step. Edit request (including an edited improved prompt) reruns PRE and requires new intent approval. Previous intent and response evidence remains in the read-only trace as superseded. Late provider results are recorded separately and never become current. Mode switches preserve valid intent and require confirmation when superseding response-dependent work.

Needs review is counted separately. Resolve uncertainty first reassesses existing evidence; a narrowly targeted AI question requires explicit approval and still requires a separate send action. An uncertainty-only result can end as Completed with review items. Terminal interactions remain read-only and have no Resume action.

For a zero-live-call hands-on check, start the existing development stub runner. Run PRE, send the original, generate a stub answer, pause, reload, and resume. Edit the request and save it; confirm the old answer disappears from the workspace and remains labeled Superseded evidence in History. The stub remains deliberately scenario-specific; automated tests exercise failure and uncertainty cases with separate deterministic providers.


## Final hands-on review

The learner approved the final hands-on review on 2026-10-12. Run one server at a time on a chosen port. If port 8000 is occupied, stop that server in its terminal with Ctrl+C or use `--port 8001` and open the matching address. Restart an existing server to load code changes; the commands above do not enable automatic reload.

Expand the first-use guide, complete the flow, inspect requirement evidence, and visit Interactions. Check pause/reload/resume before completion, then confirm completed records have no Resume action. Review at a narrow browser width as well as desktop size.

Known limits: one shared History, no accounts; conservative Replay compatibility; model judgments can vary despite schema/evidence validation; no live repair/VERIFY validation has been performed in the final polish pass. The genuine response and the prior live POST result are documented in `devpost/live-verification.md`. Deterministic tests establish orchestration and boundaries, not general semantic accuracy. Gemini browser acceptance and deployment are complete; submission remains pending.


### Revised workbench hands-on path

The desktop view uses equal request/answer columns. Start with Review my request on the left. After approval, send the request (or load the captured Replay response). Attention moves to AI answer ready on the right: read it, then use Check this answer below it. Fix only what's missing prepares a follow-up on the left. Send follow-up returns a new answer on the right; Verify result shows actual before/after counts. On narrow screens those sections stack in interaction order. The learner approved this interface, including full new-case orientation and compact persistent active-case orientation.

## Build completion and reference map

All four build slices, final hands-on review, and the Skill Pack learning wrap-up are complete. Open [the standalone app map](devpost/app-map.html) locally for the finished code route and reusable verification practice. Planning documents remain approved; completion and test evidence are recorded in [the build checklist](devpost/checklist.md). Subsequent authorized milestones are recorded in devpost/finalization.md.

## Post-build live refinement and observability

The completed 5-build milestone remains historical and unchanged. The separately authorized refinement is recorded in [post-build-live-ai.md](devpost/post-build-live-ai.md).

Each live model attempt records provider/model, purpose, response ID, duration, token usage (including reasoning tokens where returned), and outcome. These typed records persist with the interaction snapshot and event trace, including failed and late results. Usage unavailable after a process/network interruption remains unknown; it is not inferred as zero. Engineering summaries expose the number of calls with known usage and sum only known values. No public quality score, dashboard, or billing is implemented.

Read an existing interaction without model calls:

```powershell
.\.venv\Scripts\python.exe -m devtools.interaction_report path/to/interaction.sqlite3 INTERACTION_ID
```

`devtools.public_live_verify` is a one-attempt, six-call validation harness that uses normal API actions and refuses an existing evidence directory. It requires explicit live-call authorization; do not rerun or remove its evidence directory to obtain another attempt.

## Gemini CLI extension v0.1 — deterministic checkpoint

The separately approved Gemini milestone now has a thin local adapter with BeforeAgent request review, AfterAgent answer review, a technical manual fallback and separate experimental storage. See [extension setup and boundaries](extensions/pickylens/README.md) and [the deterministic checkpoint](devpost/gemini-extension-checkpoint.md). Earlier statements that Gemini had not started describe the completed 5-build milestone. Live Gemini/OpenAI validation is still pending separate approval; 6-ship has not started.

## Judge Pass access (finalization candidate)

The Gemini extension requires a Judge Pass; the normal Web demo automatically receives a bounded anonymous session. An operator creates a bounded code with `.\.venv\Scripts\python.exe -m devtools.issue_judge_pass --operations 30 --hours 72` and shares it privately. This command prints a bearer credential: never put its output in Git, screenshots, logs, or public documents. Extension users enter it in the extension toolbar popup. Web visitors land directly in the live workspace. Anonymous History is scoped to the current browser session; expired or cleared sessions cannot reopen prior records. Use sample work only.

Defaults: 30 provider operations per issued pass, 72-hour expiration, 6 provider calls per rolling minute per pass, and a persistent global lifetime ceiling of 200 calls. Failed attempts consume a reservation. Each call has a 60,000-character serialized-context ceiling and a 6,000-output-token cap. These are bounded-call/token controls, not exact dollar accounting. Browser POST currently costs two calls (request extraction then evaluation); PRE and repair each cost one. Exhaustion blocks provider execution and never falls back to Replay. Protect the access database and do not delete it to reset spending inadvertently.

Operator environment variables: `PICKYLENS_ACCESS_DB`, `PICKYLENS_GLOBAL_OPERATIONS`, `PICKYLENS_OPERATIONS_PER_MINUTE`. Supply these as process environment variables, including through VESTA systemd's protected `/etc/neovantia/secrets/pickylens/runtime.env`. Keep `OPENAI_API_KEY` there as well; deployed repositories do not need `.env`. Use HTTPS, preserve forwarded scheme/host only from the trusted reverse proxy, and keep the database outside the public web root. Local development continues to load model configuration from ignored `.env` with OS precedence.

## Optional Gemini browser extension

See `extensions/browser/README.md`. The new candidate uses composer PRE and an explicit Check this answer action; it does not infer automatic POST completion. The old browser spike and CLI adapters remain evidence/optional integrations.

The operator packages one exact deployed HTTPS backend origin using `python -m devtools.package_browser https://YOUR-DEPLOYED-HOST work/pickylens-browser.zip`. Replace the example with the actual verified deployment. The ZIP has no secrets and requests only that backend plus Gemini access. Judges install the ZIP unpacked and enter a Judge Pass; they do not run this packaging command or install developer tools.

Privacy: Web interactions and evidence are saved in server SQLite and visible only to their anonymous browser session. Browser reviews are transient in page memory; submitted text is sent to the backend and OpenAI with API storage disabled. Disabling API storage does not promise zero provider retention. The pass ledger stores token hashes, expiration and call reservations, not prompts. Do not use confidential client material in this shared hackathon instance.

Browser live acceptance and HTTPS deployment passed on 2026-10-23. 6-ship is in progress; video, public repository and learner-written submission remain pending.


### Global token circuit breaker

`PICKYLENS_GLOBAL_TOKEN_BUDGET=2000000` adds a cumulative input-plus-output token ceiling alongside the call ceiling. Each call atomically reserves 300,000 tokens; known usage settles to the reported total. Unknown usage (including interrupted calls) retains its reservation. Concurrent pending calls therefore consume capacity before invoking OpenAI. The provider bounds serialized input/schema size and output tokens; admission may stop conservatively with unused budget below a full reservation. Persist the ledger across restarts. Set the global token budget to zero for an immediate fail-closed stop. Reservations preserve model, purpose, latency and usage metadata; model reasoning configuration remains in protected runtime configuration and validation evidence.

Canonical deployment target: https://pickylens.neovantia.live, with API paths on the same origin. HTTPS access and fail-closed Judge Pass behavior have been verified without additional inference.


## Anonymous public Web access

The public Web workspace requires no credential. A random HttpOnly SameSite=Strict cookie is issued automatically (Secure over HTTPS). Defaults: 12 provider operations per session / 24 hours, 6 operations per minute per session and IP, 30 per IP per rolling 24 hours. IPs are stored as keyed hashes; clearing cookies does not reset the IP allowance. Limits are configured through PICKYLENS_ANONYMOUS_OPERATIONS, PICKYLENS_ANONYMOUS_HOURS, PICKYLENS_ANONYMOUS_PER_MINUTE and PICKYLENS_ANONYMOUS_IP_OPERATIONS.

Web and extension reservations share the same persistent 200-call and 2,000,000-token global breakers. Exhaustion returns “Public demo allowance reached. Please try again later.” No Replay/stub fallback exists. Requests from other origins are rejected. Only the trusted loopback proxy may supply forwarded client addresses. Anonymous cookies never authorize extension endpoints, which require Bearer Judge Pass authentication. Earlier shared-History descriptions refer to the prior controlled-demo deployment; existing records are preserved but are not exposed to anonymous visitors.
