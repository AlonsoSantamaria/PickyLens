"""Operation-local call collection; no mutable provider-wide interaction state."""
from contextvars import ContextVar
calls = ContextVar("model_calls", default=None)
