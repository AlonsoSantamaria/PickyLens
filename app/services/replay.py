"""Deterministic comparison of explicitly established canonical intent data.

Display wording and interaction-local requirement IDs are deliberately excluded.
Unknown mappings fail closed. This module performs no provider calls.
"""
from pydantic import Field
from app.core.contracts import Contract


class CanonicalRequirement(Contract):
    key: str
    constraints: dict[str, str | int | bool] = Field(default_factory=dict)


class CanonicalIntent(Contract):
    scenario_id: str
    scenario_version: int
    requirements: list[CanonicalRequirement]
    accepted_clarifications: dict[str, str]
    constraints: dict[str, str | int | bool]
    decisions: dict[str, str]
    mapping_established: bool


def compatible(current: CanonicalIntent, captured: CanonicalIntent) -> bool:
    if not current.mapping_established or not captured.mapping_established:
        return False
    def signature(intent):
        keys = [r.key for r in intent.requirements]
        if not keys or len(keys) != len(set(keys)):
            return None
        data = intent.model_dump(mode="json")
        data["requirements"] = sorted(data["requirements"], key=lambda r: r["key"])
        # JSON keeps booleans distinct from integers; Python equality does not.
        import json
        return json.dumps(data, sort_keys=True, separators=(",", ":"))
    left, right = signature(current), signature(captured)
    return left is not None and left == right


from pathlib import Path
import json
import hashlib
from app.core.contracts import Answer


def load_fixture():
    data = json.loads((Path(__file__).resolve().parents[1] / "fixtures/consultant_replay.v1.json").read_text(encoding="utf-8"))
    if hashlib.sha256(data["response"]["text"].encode()).hexdigest() != data["sha256"]:
        raise ValueError("Replay fixture integrity check failed")
    return data


def acquire(intent):
    fixture = load_fixture()
    expected = CanonicalIntent.model_validate(fixture["canonical_intent"])
    # Binding is assigned only by explicit acceptance of the displayed canonical preset.
    if intent.replay_scenario != fixture["scenario_id"] or intent.accepted_clarifications:
        raise ValueError("Replay intent is incompatible. Reset to the canonical demo scenario or continue in Live Model.")
    binding = CanonicalIntent.model_validate(intent.replay_binding) if intent.replay_binding else None
    if not binding or not compatible(binding, expected) or sorted(r.source for r in intent.requirements) != sorted(fixture["canonical_keys"]):
        raise ValueError("Replay requirement binding is uncertain. Reset or continue in Live Model.")
    answer = Answer.model_validate(fixture["response"])
    answer.metadata["acquisition"] = "replay"
    return answer
