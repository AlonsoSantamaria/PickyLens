"""Local-only Slice 1 checkpoint. No SDK, credentials, or live model calls."""
import os
from app.main import create_app
from devtools.stub_provider import StubProvider

app = create_app(StubProvider(), os.getenv("PICKYLENS_DB_PATH", "data/slice1-stub.sqlite3"))
