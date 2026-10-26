from app.core.contracts import NextProposal, Status
from app.core.failures import ReviewFailure


async def generate(provider, intent, post, answer, approved_uncertainty=()):
    expected = {r.requirement_id:r.text for r in intent.requirements}
    if (post.intent_version != intent.version or post.phase not in {"post","verify"}
        or len(post.assessments) != len(expected)
        or {a.requirement_id:a.requirement_text for a in post.assessments} != expected):
        raise ReviewFailure("semantic_validation", "next_intent_mismatch", "next")
    allowed = {a.requirement_id for a in post.assessments if a.status in {Status.partial, Status.missing}}
    uncertain = {a.requirement_id for a in post.assessments if a.status == Status.needs_review}
    if not set(approved_uncertainty) <= uncertain:
        raise ValueError("Uncertainty approval is not current")
    allowed |= set(approved_uncertainty)
    if not allowed:
        raise ValueError("No repairable gaps were identified")
    result = await provider.generate_structured({"intent": intent.model_dump(mode="json"),
        "assessment": post.model_dump(mode="json"), "answer": answer.model_dump(mode="json"),
        "allowed_targets": sorted(allowed)}, NextProposal, "next")
    if not isinstance(result, NextProposal) or not result.text.strip() or not result.target_requirement_ids or len(result.target_requirement_ids) != len(set(result.target_requirement_ids)) or not set(result.target_requirement_ids) <= allowed:
        raise ReviewFailure("semantic_validation", "unapproved_followup_targets", "next")
    return result
