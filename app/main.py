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


def create_app(provider=None, db_path=None):
    settings = load_settings()
    provider = provider or (OpenAIProvider(settings) if settings.api_key.get_secret_value() else UnconfiguredProvider())
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

    def render(request, template, **context):
        return templates.TemplateResponse(request=request, name=template, context={"stub": provider.test_stub, **context})

    @app.get("/", response_class=HTMLResponse)
    async def workspace(request: Request, interaction: str | None = None):
        saved = repository.get(interaction) if interaction else None
        if saved and saved.terminal:
            return RedirectResponse(f"/interactions/{interaction}")
        return render(request, "workspace.html", snapshot=saved, prompt=saved.current_request if saved else PROMPT, description=DESCRIPTION, demo=load_fixture())

    @app.get("/interactions", response_class=HTMLResponse)
    async def history(request: Request):
        return render(request, "interactions.html", interactions=repository.list())

    @app.get("/interactions/{id}", response_class=HTMLResponse)
    async def detail(request: Request, id: str):
        return render(request, "interaction_detail.html", snapshot=repository.get(id), events=repository.trace(id))

    @app.get("/api/interactions/{id}")
    async def read(id: str):
        return repository.get(id)

    @app.post("/api/interactions/pre")
    async def start(action: Action):
        return await service.start(action)

    @app.post("/api/interactions/{id}/{name}")
    async def act(id: str, name: str, action: Action):
        return await service.act(id, name, action)

    return app


app = create_app()
