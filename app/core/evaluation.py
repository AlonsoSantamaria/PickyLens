from app.core.contracts import Evaluation, Status


async def evaluate(provider, intent, answers, phase):
    if not intent.requirements:
        raise ValueError("No approved requirements can be evaluated reliably")
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
        for finding in item.consistency_findings:
            if finding.certainty not in {"confirmed", "uncertain"}:
                raise ValueError("Invalid consistency certainty")
            if not finding.explanation.strip():
                raise ValueError("Consistency finding requires an explanation")
            if finding.certainty == "confirmed" and len({(e.response_id, e.excerpt) for e in finding.evidence}) < 2:
                raise ValueError("Confirmed contradiction requires both conflicting claims")
            item.evidence.extend(e for e in finding.evidence if e not in item.evidence)
        confirmed = [f for f in item.consistency_findings if f.certainty == "confirmed"]
        uncertain = [f for f in item.consistency_findings if f.certainty == "uncertain"]
        if confirmed:
            item.status = Status.partial
            item.explanation = " ".join(f.explanation for f in confirmed)
        elif uncertain:
            item.status = Status.needs_review
            item.uncertainty_reason = " ".join(f.explanation for f in uncertain)
        if item.status == Status.complete and not item.evidence:
            raise ValueError("Complete assessment requires evidence")
        if item.status == Status.needs_review and not item.uncertainty_reason:
            raise ValueError("Uncertain assessment requires explanation")
        for evidence in item.evidence:
            if not evidence.excerpt.strip() or evidence.excerpt not in source.get(evidence.response_id, ""):
                raise ValueError("Evidence is not present in its referenced answer")
    return result
