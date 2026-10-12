from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field


def uid():
    return str(uuid4())


def now():
    return datetime.now(timezone.utc).isoformat()


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Status(StrEnum):
    complete = "complete"
    partial = "partial"
    missing = "missing"
    needs_review = "needs_review"


class Requirement(Contract):
    requirement_id: str = Field(default_factory=uid)
    text: str
    source: str = "original_request"


class Finding(Contract):
    title: str
    explanation: str


class Clarification(Contract):
    key: str
    question: str
    options: list[str]
    required: bool = True


class PREProposal(Contract):
    readiness: str
    findings: list[Finding]
    clarifications: list[Clarification]
    requirements: list[Requirement]
    improved_prompt: str


class ApprovedIntent(Contract):
    version: int
    original_request: str
    approved_prompt: str
    approved_at: str = Field(default_factory=now)
    approval_action: str
    accepted_clarifications: dict[str, str]
    requirements: list[Requirement]


class Answer(Contract):
    response_id: str = Field(default_factory=uid)
    text: str
    metadata: dict[str, str] = Field(default_factory=dict)


class Evidence(Contract):
    response_id: str
    excerpt: str
    location: str


class Assessment(Contract):
    requirement_id: str
    requirement_text: str
    status: Status
    explanation: str
    evidence: list[Evidence]
    uncertainty_reason: str | None = None


class Evaluation(Contract):
    intent_version: int
    phase: str
    assessments: list[Assessment]

    def counts(self):
        return {s.value: sum(a.status == s for a in self.assessments) for s in Status}


class NextProposal(Contract):
    text: str
    target_requirement_ids: list[str]


class Snapshot(Contract):
    schema_version: int = 1
    interaction_id: str = Field(default_factory=uid)
    title: str = "Operational alternatives recommendation"
    original_request: str
    current_request: str
    selected_prompt: str | None = None
    mode: str = "live"
    stage: str = "pre"
    lifecycle_status: str = "In progress"
    revision: int = 0
    last_event_sequence: int = 0
    created_at: str = Field(default_factory=now)
    updated_at: str = Field(default_factory=now)
    pre: PREProposal | None = None
    accepted_clarifications: dict[str, str] = Field(default_factory=dict)
    intent: ApprovedIntent | None = None
    answer: Answer | None = None
    post: Evaluation | None = None
    next: NextProposal | None = None
    followup_draft: str | None = None
    followup_answer: Answer | None = None
    verification: Evaluation | None = None
    failure: str | None = None
    test_stub: bool = False

    @property
    def terminal(self):
        return self.lifecycle_status in {"Complete after first response", "Complete after verification", "Completed with review items"}


class EventPayload(Contract):
    snapshot: Snapshot
    operation_id: str


class Action(Contract):
    operation_id: str = Field(min_length=1)
    expected_revision: int | None = None
    request_text: str | None = None
    mode: str = "live"
    choice: str | None = None
    prompt: str | None = None
    clarifications: dict[str, str] = Field(default_factory=dict)
    confirmed_red: bool = False
