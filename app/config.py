import os
from pathlib import Path
from dotenv import dotenv_values
from pydantic import BaseModel, ConfigDict, SecretStr

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_key: SecretStr
    model: str
    reasoning_effort: str
    provider: str
    db_path: str
    timeout: float


def load_settings(root=ROOT, environ=None):
    env = dict(os.environ if environ is None else environ)
    values = {}
    if env.get("PICKYLENS_ENV", "development") == "development":
        values = dict(dotenv_values(Path(root) / ".env", encoding="utf-8-sig", interpolate=False))
    values.update(env)
    return Settings(api_key=SecretStr(values.get("OPENAI_API_KEY") or ""),
        model=values.get("PICKYLENS_MODEL") or "gpt-5.6-sol",
        reasoning_effort=values.get("PICKYLENS_REASONING_EFFORT") or "low",
        provider=values.get("PICKYLENS_PROVIDER") or "openai",
        db_path=values.get("PICKYLENS_DB_PATH") or "data/pickylens.sqlite3",
        timeout=float(values.get("PICKYLENS_API_TIMEOUT_SECONDS") or 120))
