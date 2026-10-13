"""Gemini CLI 0.63 hook boundary. Host input never becomes shell code."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class HookInput(BaseModel):
    model_config = ConfigDict(extra="ignore")
    session_id: str = Field(min_length=1, max_length=512)
    transcript_path: str = Field(max_length=4096)
    cwd: str = Field(min_length=1, max_length=4096)
    hook_event_name: Literal["BeforeAgent", "AfterAgent"]
    timestamp: datetime
    prompt: str = Field(max_length=200000)
    prompt_response: str = Field(default="", max_length=1000000)
    stop_hook_active: bool = False

    @field_validator("timestamp")
    @classmethod
    def timezone_required(cls, value):
        if value.tzinfo is None:
            raise ValueError("Hook timestamp requires a timezone")
        return value


def advisory(message):
    # Never emit deny, continue=false, context injection or a retry instruction.
    return {"decision": "allow", "systemMessage": message}
