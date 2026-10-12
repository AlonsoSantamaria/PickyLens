from typing import Protocol
from pydantic import BaseModel
from app.core.contracts import Answer


class Provider(Protocol):
    test_stub: bool

    async def generate_structured(self, context: dict, result_schema: type[BaseModel], purpose: str) -> BaseModel: ...

    async def generate_text(self, context: dict, purpose: str) -> Answer: ...
