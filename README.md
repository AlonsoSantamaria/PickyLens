# PickyLens

Quality-check the whole AI interaction.

## Slice 1 checkpoint

This implementation is the first working golden path, not the completed hackathon build. It uses real SQLite persistence and a **clearly labeled deterministic development stub** for all AI behavior. Stub outputs and evaluations are synthetic and scenario-specific, not real model evidence or a captured Replay Demo. No API key is needed and no live calls are made.

From PowerShell in `C:\__Dev\Neovantia\Apps\PickyLens`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn devtools.stub_app:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/. Use the prefilled consultant scenario. Review, select **Lowest upfront cost**, save the clarification, approve the improved prompt, generate the first response, and run POST. Generate a targeted follow-up, optionally edit/save it, explicitly send it, and verify both responses. Open Interactions and inspect the saved evidence and ordered trace. Restarting the server retains saved work in `data/slice1-stub.sqlite3`.

The stub is deliberately narrow. Editing the request does not make its synthetic semantic behavior general-purpose. The banner and stored metadata distinguish these records from live/replay interactions. Changing an earlier request, uncertainty-resolution controls, retry/recovery, and safe mode switching are later slices. The app does not yet expose those incomplete controls.

The production assembly is `app.main:app`; real OpenAI integration and the genuine Replay fixture are not enabled during Slice 1. The development stub is injected by `devtools.stub_app`, not selectable through a product setting.

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
