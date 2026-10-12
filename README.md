# PickyLens

Quality-check the whole AI interaction.

## Slice 2 checkpoint

The application now supports genuine Replay Demo and Live Model through the configured OpenAI adapter. From the project directory, run:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Set `OPENAI_API_KEY` locally outside source control. Open http://127.0.0.1:8000/. Review the canonical scenario, inspect PRE and the canonical requirement list, then explicitly approve the canonical Replay request. Generate the captured first answer and run POST. Expand the cost/comparison evidence, generate a targeted repair, review it, send it, and verify the combined responses. Each review and repair action uses the configured live provider; opening the app makes no model calls. Replay replaces only first-answer acquisition. Dynamic assessments can vary; no expected result is embedded in the fixture.

The fixture preserves the unchanged final-batch Attempt 1 answer, exact capture request, model, timestamps, response ID, usage, and a SHA-256 integrity hash. It contains conflicting cost statements. Canonical compatibility uses structured keys, constraints, decisions, and explicit approval; display wording is not compared. Arbitrary free-text mappings remain uncertain and require resetting to the canonical preset or using Live Model. The preset explicitly excludes PRE clarification choices; choose Live to retain changed intent.

Mode switches after a response require confirmation and preserve superseded evidence in History. Request revision, comprehensive retries/recovery, and uncertainty-resolution controls remain Slice 3 work. Slice 2 verification details are in `devpost/live-verification.md`.

## Deterministic development checkpoint

This implementation is the first working golden path, not the completed hackathon build. It uses real SQLite persistence and a **clearly labeled deterministic development stub** for all AI behavior. Stub outputs and evaluations are synthetic and scenario-specific, not real model evidence or a captured Replay Demo. No API key is needed and no live calls are made.

From PowerShell in `C:\__Dev\Neovantia\Apps\PickyLens`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn devtools.stub_app:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/. Use the prefilled consultant scenario. Review, select **Lowest upfront cost**, save the clarification, approve the improved prompt, generate the first response, and run POST. Generate a targeted follow-up, optionally edit/save it, explicitly send it, and verify both responses. Open Interactions and inspect the saved evidence and ordered trace. Restarting the server retains saved work in `data/slice1-stub.sqlite3`.

The stub is deliberately narrow. Editing the request does not make its synthetic semantic behavior general-purpose. The banner and stored metadata distinguish these records from live/replay interactions. Changing an earlier request, uncertainty-resolution controls, retry/recovery, are later slices. The app does not yet expose those incomplete controls.

The real application assembly is `app.main:app`. The development stub is injected by `devtools.stub_app`, not selectable through a product setting.

## Setup with the existing Python interpreter

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

For VESTA, set `PICKYLENS_ENV=production` in the service environment to disable repository dotenv loading. Plan to use systemd `EnvironmentFile=/etc/neovantia/secrets/pickylens/runtime.env` with the same variable names and restrictive permissions. Do not place deployment secrets in the checkout. This is deployment documentation only; no server changes have been made.

The bounded Slice 2 verification harness is `python -m devtools.live_verify`; it records attempts and usage under ignored `work/live-verification/`, disables SDK retries, and refuses automatic reruns of an existing capture. Never run it without an authorized live-call budget.
