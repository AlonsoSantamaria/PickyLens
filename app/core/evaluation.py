from app.core.contracts import Evaluation, Status


async def evaluate(provider, intent, answers, phase):
    result = await provider.generate_structured({"intent": intent.model_dump(mode="json"),
        "answers": [a.model_dump(mode="json") for a in answers], "phase": phase}, Evaluation, "evaluate")
    expected = {r.requirement_id: r.text for r in intent.requirements}
    ids = [a.requirement_id for a in result.assessments]
    if len(ids) != len(set(ids)) or set(ids) != set(expected) or result.intent_version != intent.version or result.phase != phase:
        raise ValueError("Assessment coverage does not match approved intent")
    source = {a.response_id: a.text for a in answers}
    for item in result.assessments:
        if item.requirement_text != expected[item.requirement_id]:
            raise ValueError("Assessment changed requirement text")
        if item.status == Status.complete and not item.evidence:
            raise ValueError("Complete assessment requires evidence")
        if item.status == Status.needs_review and not item.uncertainty_reason:
            raise ValueError("Uncertain assessment requires explanation")
        for evidence in item.evidence:
            if not evidence.excerpt.strip() or evidence.excerpt not in source.get(evidence.response_id, ""):
                raise ValueError("Evidence is not present in its referenced answer")
    return result
