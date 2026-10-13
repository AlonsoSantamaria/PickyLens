# PickyLens

Quality-check the whole AI interaction.

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

From PowerShell in `C:\__Dev\Neovantia\Apps\PickyLens`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn devtools.stub_app:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/. Use the prefilled consultant scenario. Review, select **Lowest upfront cost**, save the clarification, choose Use improved request, send the request, read the first response on the right, and choose Check this answer. Generate a targeted follow-up, optionally edit/save it, explicitly send it, and verify both responses. Open Interactions and inspect the saved evidence and ordered trace. Restarting the server retains saved work in `data/slice1-stub.sqlite3`.

The stub is deliberately narrow. Editing the request does not make its synthetic semantic behavior general-purpose. The banner and stored metadata distinguish these records from live/replay interactions. Recovery and request revision use the same coordinator as the real application.

The real application assembly is `app.main:app`. The development stub is injected by `devtools.stub_app`, not selectable through a product setting.

## First-time setup (skip when .venv already exists)

```powershell
& 'C:\Program Files\Python314\python.exe' -m venv .venv
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

For VESTA, set `PICKYLENS_ENV=production` in the service environment to disable repository dotenv loading. Plan to use systemd `EnvironmentFile=/etc/neovantia/secrets/pickylens/runtime.env` with the same variable names and restrictive permissions. Do not place deployment secrets in the checkout. Protect the deployed single-user instance with HTTP Basic Authentication or equivalent access control at the VESTA reverse proxy; keep application authentication out of the MVP. This is deployment documentation only; no server changes have been made.

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

Known limits: one shared History, no accounts; conservative Replay compatibility; model judgments can vary despite schema/evidence validation; no live repair/VERIFY validation has been performed in the final polish pass. The genuine response and the prior live POST result are documented in `devpost/live-verification.md`. Deterministic tests establish orchestration and boundaries, not general semantic accuracy. Gemini integration and deployment/submission work remain unstarted.


### Revised workbench hands-on path

The desktop view uses equal request/answer columns. Start with Review my request on the left. After approval, send the request (or load the captured Replay response). Attention moves to AI answer ready on the right: read it, then use Check this answer below it. Fix only what's missing prepares a follow-up on the left. Send follow-up returns a new answer on the right; Verify result shows actual before/after counts. On narrow screens those sections stack in interaction order. The learner approved this interface, including full new-case orientation and compact persistent active-case orientation.

## Build completion and reference map

All four build slices, final hands-on review, and the Skill Pack learning wrap-up are complete. Open [the standalone app map](devpost/app-map.html) locally for the finished code route and reusable verification practice. Planning documents remain approved; completion and test evidence are recorded in [the build checklist](devpost/checklist.md). Gemini and 6-ship require separate approval and have not started.

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
