"""Provider-neutral wire contracts. Canonical identities never come from the model."""
import json
from pydantic import Field, create_model, ValidationError
from app.core.contracts import (Contract, Finding, Clarification, Requirement, PREProposal,
    Status, Assessment, Evidence, ConsistencyFinding, Evaluation, NextProposal, FailureDiagnostic)
from app.core.failures import ReviewFailure, validation_diagnostics


class ClarificationDraft(Contract):
    question: str
    options: list[str]
    required: bool


class RequestDraft(Contract):
    readiness: str
    findings: list[Finding]
    clarifications: list[ClarificationDraft]
    requirements: list[str]
    improved_prompt: str


class EvidenceDraft(Contract):
    answer_index: int = Field(strict=True)
    excerpt: str
    location: str


class ConflictDraft(Contract):
    certainty: str
    explanation: str
    evidence: list[EvidenceDraft]


class Judgment(Contract):
    status: Status
    explanation: str
    evidence: list[EvidenceDraft]
    uncertainty_reason: str | None = None
    consistency_findings: list[ConflictDraft] = Field(default_factory=list)


class FollowupDraft(Contract):
    text: str


class ObjectPairs(dict):
    def __init__(self, pairs):
        super().__init__()
        self.duplicates = set()
        for key, value in pairs:
            if key in self: self.duplicates.add(key)
            self[key] = value


def duplicate_nested(value):
    if isinstance(value, ObjectPairs):
        return bool(value.duplicates) or any(duplicate_nested(v) for v in value.values())
    return isinstance(value, list) and any(duplicate_nested(v) for v in value)


def load_object(text, stage):
    try: result = json.loads(text, object_pairs_hook=ObjectPairs)
    except (ValueError, TypeError): raise ReviewFailure("structured_parse", "invalid_json", stage) from None
    if not isinstance(result, dict):
        raise ReviewFailure("structured_parse", "invalid_top_level", stage)
    return result


def uncertain(requirement, reason):
    return Assessment(requirement_id=requirement["requirement_id"], requirement_text=requirement["text"],
        status=Status.needs_review, explanation=reason, uncertainty_reason=reason, evidence=[])


def wire_contract(context, schema, purpose):
    """Return model context/schema and a local decoder. No additional inference."""
    if schema is PREProposal:
        def decode(text):
            raw = load_object(text, "pre")
            if duplicate_nested(raw): raise ReviewFailure("structured_parse", "duplicate_pre_fields", "pre")
            draft = RequestDraft.model_validate(raw)
            return PREProposal(readiness=draft.readiness, findings=draft.findings,
                clarifications=[Clarification(key=f"clarification_{i}", **c.model_dump()) for i,c in enumerate(draft.clarifications)],
                requirements=[Requirement(text=t, source="original_request") for t in draft.requirements],
                improved_prompt=draft.improved_prompt)
        return context, RequestDraft, decode
    if schema is NextProposal:
        def decode(text):
            raw = load_object(text, "next")
            if duplicate_nested(raw): raise ReviewFailure("structured_parse", "duplicate_next_fields", "next")
            draft = FollowupDraft.model_validate(raw)
            return NextProposal(text=draft.text, target_requirement_ids=list(context["allowed_targets"]))
        return context, FollowupDraft, decode
    if schema is not Evaluation:
        return context, schema, schema.model_validate_json
    requirements = context["intent"]["requirements"]
    slots = {f"r{i}": r for i,r in enumerate(requirements)}
    wire_schema = create_model("RequirementJudgments", __base__=Contract,
        **{key:(Judgment | None, None) for key in slots})
    model_context = {"requirements": {k:r["text"] for k,r in slots.items()},
        "approved_prompt":context["intent"]["approved_prompt"],
        "accepted_clarifications":context["intent"]["accepted_clarifications"],
        "answers":[{"answer_index":i,"text":a["text"]} for i,a in enumerate(context["answers"])],
        "task":"Verify the combined result; explicit corrections may supersede earlier claims." if context["phase"]=="verify" else "Check the answer."}
    def decode(text):
        raw = load_object(text, context["phase"])
        if raw and not set(raw).intersection(slots):
            raise ReviewFailure("semantic_validation", "unmappable_assessment_response", context["phase"])
        result = Evaluation(intent_version=context["intent"]["version"],phase=context["phase"],assessments=[])
        def diagnostic(code, requirement_id=None):
            result.diagnostics.append(FailureDiagnostic(failure_layer="semantic_validation",stage=context["phase"],
                validation_code=code,requirement_id=requirement_id))
        if set(raw)-set(slots): diagnostic("unknown_assessment_slot")
        def evidence(candidate):
            index=candidate.answer_index
            response_id=context["answers"][index]["response_id"] if 0 <= index < len(context["answers"]) else ""
            return Evidence(response_id=response_id,excerpt=candidate.excerpt,location=candidate.location)
        for key,requirement in slots.items():
            code = None
            if key not in raw or raw[key] is None: code="missing_assessment"
            elif key in raw.duplicates or duplicate_nested(raw[key]): code="duplicate_assessment_fields"
            else:
                try: draft=Judgment.model_validate(raw[key])
                except ValidationError as exc:
                    code="invalid_assessment_structure"
                    result.diagnostics.extend(validation_diagnostics(exc,Judgment,context["phase"],
                        "semantic_validation",requirement["requirement_id"]))
            if code:
                diagnostic(code,requirement["requirement_id"])
                result.assessments.append(uncertain(requirement,"PickyLens could not validate this requirement's assessment. Review is needed."))
                continue
            result.assessments.append(Assessment(requirement_id=requirement["requirement_id"],requirement_text=requirement["text"],
                status=draft.status,explanation=draft.explanation,uncertainty_reason=draft.uncertainty_reason,
                evidence=[evidence(e) for e in draft.evidence],consistency_findings=[ConsistencyFinding(
                    certainty=f.certainty,explanation=f.explanation,evidence=[evidence(e) for e in f.evidence]) for f in draft.consistency_findings]))
        return result
    return model_context, wire_schema, decode
