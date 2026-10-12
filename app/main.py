import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.core.contracts import Action
from app.config import load_settings
from app.providers.openai_adapter import OpenAIProvider
from app.services.replay import load_fixture
from app.storage.repository import Repository, Conflict
from app.services.interactions import Interactions, StageFailure
from app.services.scenario import PROMPT, DESCRIPTION

BASE = Path(__file__).parent


class UnconfiguredProvider:
    test_stub = False

    async def generate_structured(self, *args, **kwargs):
        raise ValueError("Configure OPENAI_API_KEY outside source control to run model-backed reviews.")

    async def generate_text(self, *args, **kwargs):
        raise ValueError("Configure OPENAI_API_KEY outside source control.")


def create_app(provider=None, db_path=None, *, internal_tools=None):
    settings = load_settings()
    provider = provider or (OpenAIProvider(settings) if settings.api_key.get_secret_value() else UnconfiguredProvider())
    internal_tools = provider.test_stub if internal_tools is None else internal_tools
    repository = Repository(db_path or load_settings().db_path)
    repository.recover_interrupted()
    service = Interactions(repository, provider)
    app = FastAPI(title="PickyLens")
    app.state.repository, app.state.provider = repository, provider
    templates = Jinja2Templates(directory=str(BASE / "templates"))
    app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")

    @app.exception_handler(StageFailure)
    async def stage_failure(request, exc):
        return JSONResponse({"detail": str(exc), "snapshot": exc.snapshot.model_dump(mode="json")}, status_code=exc.status_code)

    @app.exception_handler(KeyError)
    async def missing(request, exc):
        return JSONResponse({"detail": "Interaction not found"}, status_code=404)

    @app.exception_handler(Conflict)
    async def conflict(request, exc):
        data = {"detail": str(exc)}
        id = request.path_params.get("id")
        if id:
            try:
                data["snapshot"] = repository.get(id).model_dump(mode="json")
            except KeyError:
                pass
        return JSONResponse(data, status_code=409)

    @app.exception_handler(ValueError)
    async def invalid(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=422)

    def visible(snapshot):
        return internal_tools or (snapshot.mode == "live" and not snapshot.test_stub)

    def public_record(id):
        snapshot = repository.get(id)
        if not visible(snapshot):
            raise KeyError(id)
        return snapshot

    def live_action(action, name=None):
        if not internal_tools and (action.mode != "live" or action.canonical_scenario or name in {"mode", "reset-scenario", "approve-canonical"}):
            raise ValueError("This workspace supports live AI interactions only.")

    def render(request, template, **context):
        return templates.TemplateResponse(request=request, name=template, context={"stub": provider.test_stub, "internal_tools": internal_tools, "live_configured": not isinstance(provider, UnconfiguredProvider), **context})

    @app.get("/", response_class=HTMLResponse)
    async def workspace(request: Request, interaction: str | None = None):
        saved = public_record(interaction) if interaction else None
        if saved and saved.terminal:
            return RedirectResponse(f"/interactions/{interaction}")
        return render(request, "workspace.html", snapshot=saved, prompt=saved.current_request if saved else PROMPT, description=DESCRIPTION, demo=load_fixture() if internal_tools else None)

    @app.get("/interactions", response_class=HTMLResponse)
    async def history(request: Request):
        return render(request, "interactions.html", interactions=[s for s in repository.list() if visible(s)])

    @app.get("/interactions/{id}", response_class=HTMLResponse)
    async def detail(request: Request, id: str):
        return render(request, "interaction_detail.html", snapshot=public_record(id), events=repository.trace(id))

    @app.get("/api/interactions/{id}")
    async def read(id: str):
        return public_record(id)

    @app.post("/api/interactions/pre")
    async def start(action: Action):
        live_action(action)
        if isinstance(provider, UnconfiguredProvider):
            return JSONResponse({"detail": "Live AI is not configured. Ask the operator to configure the AI service, then try again."}, status_code=503)
        return await service.start(action)

    @app.post("/api/interactions/{id}/{name}")
    async def act(id: str, name: str, action: Action):
        public_record(id)
        live_action(action, name)
        return await service.act(id, name, action)

    return app


app = create_app()
