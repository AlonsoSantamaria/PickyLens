import os
import hashlib
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
from app.services.judge_access import JudgeAccess, BoundedProvider, AccessDenied, principal
from app.web.browser_api import router as browser_router

BASE = Path(__file__).parent


class UnconfiguredProvider:
    test_stub = False

    async def generate_structured(self, *args, **kwargs):
        raise ValueError("Configure OPENAI_API_KEY outside source control to run model-backed reviews.")

    async def generate_text(self, *args, **kwargs):
        raise ValueError("Configure OPENAI_API_KEY outside source control.")


def create_app(provider=None, db_path=None, *, internal_tools=None, access=None):
    injected_provider = provider is not None
    settings = load_settings()
    provider = provider or (OpenAIProvider(settings) if settings.api_key.get_secret_value() else UnconfiguredProvider())
    internal_tools = provider.test_stub if internal_tools is None else internal_tools
    if access is None and not injected_provider and not internal_tools:
        access = JudgeAccess(os.environ.get("PICKYLENS_ACCESS_DB", "data/judge-access.sqlite3"),
            int(os.environ.get("PICKYLENS_GLOBAL_OPERATIONS", "200")),
            int(os.environ.get("PICKYLENS_OPERATIONS_PER_MINUTE", "6")),
            int(os.environ.get("PICKYLENS_GLOBAL_TOKEN_BUDGET", "2000000")),
            anonymous_operations=int(os.environ.get("PICKYLENS_ANONYMOUS_OPERATIONS", "12")),
            anonymous_hours=int(os.environ.get("PICKYLENS_ANONYMOUS_HOURS", "24")),
            anonymous_per_minute=int(os.environ.get("PICKYLENS_ANONYMOUS_PER_MINUTE", "6")),
            anonymous_ip_operations=int(os.environ.get("PICKYLENS_ANONYMOUS_IP_OPERATIONS", "30")),
            anonymous_ip_hours=int(os.environ.get("PICKYLENS_ANONYMOUS_IP_HOURS", "24")),
            devpost_operations=int(os.environ.get("PICKYLENS_DEVPOST_OPERATIONS", "30")),
            devpost_hours=int(os.environ.get("PICKYLENS_DEVPOST_HOURS", "72")),
            devpost_per_minute=int(os.environ.get("PICKYLENS_DEVPOST_PER_MINUTE", "6")),
            devpost_ip_operations=int(os.environ.get("PICKYLENS_DEVPOST_IP_OPERATIONS", "60")),
            devpost_ip_hours=int(os.environ.get("PICKYLENS_DEVPOST_IP_HOURS", "72")))
    unconfigured = isinstance(provider, UnconfiguredProvider)
    if access:
        provider = BoundedProvider(provider, access)
    repository = Repository(db_path or load_settings().db_path)
    repository.recover_interrupted()
    service = Interactions(repository, provider)
    app = FastAPI(title="PickyLens", docs_url=None, redoc_url=None)
    app.include_router(browser_router(provider))

    @app.exception_handler(AccessDenied)
    async def access_error(request, exc):
        return JSONResponse({"detail":str(exc)}, status_code=429)

    @app.middleware("http")
    async def judge_gate(request, call_next):
        if not access or request.url.path.startswith('/static/') or request.url.path == '/access':
            return await call_next(request)
        browser_api = request.url.path.startswith('/api/browser/')
        new_cookie = None
        devpost_arrival = request.method == 'GET' and request.url.path == '/' and request.query_params.get('ref') == 'devpost'
        if browser_api:
            bearer = request.headers.get('authorization', '')
            try:
                identity = access.validate(bearer[7:] if bearer.startswith('Bearer ') else '')
            except AccessDenied as exc:
                return JSONResponse({'detail': str(exc)}, status_code=401)
        else:
            if request.method not in {'GET','HEAD'}:
                if request.headers.get('origin') != str(request.base_url).rstrip('/'):
                    return JSONResponse({'detail':'Request origin not permitted.'}, status_code=403)
            # Uvicorn accepts forwarded client addresses only from the loopback proxy.
            identity, new_cookie = access.anonymous(request.cookies.get('pickylens_demo',''), request.client.host if request.client else 'unknown', devpost=devpost_arrival)
        ctx = principal.set(identity)
        try:
            response = await call_next(request)
            if new_cookie:
                response.set_cookie('pickylens_demo', new_cookie, httponly=True, samesite='strict',
                                    secure=request.url.scheme=='https', max_age=(access.devpost_hours if devpost_arrival else access.anonymous_hours)*3600, path='/')
            response.headers['Cache-Control'] = 'no-store'
            return response
        finally:
            principal.reset(ctx)

    @app.get('/access')
    async def access_page():
        return RedirectResponse('/', status_code=303)

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
        if access:
            with repository.connect() as db:
                row = db.execute('SELECT operation_id FROM interaction_events WHERE interaction_id=? AND sequence_number=1', (snapshot.interaction_id,)).fetchone()
            if not row or not row[0] or not row[0].startswith((principal.get() or 'unowned') + ':'):
                return False
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
        return templates.TemplateResponse(request=request, name=template, context={"stub": provider.test_stub, "internal_tools": internal_tools, "live_configured": not unconfigured, **context})

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

    def scoped_action(action):
        if access:
            return action.model_copy(update={'operation_id': principal.get() + ':' + hashlib.sha256(action.operation_id.encode()).hexdigest()})
        return action

    @app.post("/api/interactions/pre")
    async def start(action: Action):
        live_action(action)
        if unconfigured:
            return JSONResponse({"detail": "Live AI is not configured. Ask the operator to configure the AI service, then try again."}, status_code=503)
        return await service.start(scoped_action(action))

    @app.post("/api/interactions/{id}/{name}")
    async def act(id: str, name: str, action: Action):
        public_record(id)
        live_action(action, name)
        return await service.act(id, name, scoped_action(action))

    return app


app = create_app()
