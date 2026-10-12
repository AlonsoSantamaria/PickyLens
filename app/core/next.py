from app.core.contracts import NextProposal, Status


async def generate(provider, intent, post, answer, approved_uncertainty=()):
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
    if not result.text.strip() or not result.target_requirement_ids or not set(result.target_requirement_ids) <= allowed:
        raise ValueError("Follow-up targets unapproved requirements")
    return result
