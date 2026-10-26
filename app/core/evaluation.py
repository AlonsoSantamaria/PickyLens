from app.core.contracts import Evaluation, Status, FailureDiagnostic
from app.core.failures import ReviewFailure
from app.core.model_contracts import uncertain


async def evaluate(provider, intent, answers, phase):
    ids = [r.requirement_id for r in intent.requirements]
    if not ids or len(ids) != len(set(ids)) or phase not in {"post", "verify"}:
        raise ReviewFailure("semantic_validation", "invalid_canonical_intent", phase)
    if not answers or len({a.response_id for a in answers}) != len(answers):
        raise ReviewFailure("semantic_validation", "ambiguous_answer_sources", phase)
    candidate = await provider.generate_structured({"intent":intent.model_dump(mode="json"),
        "answers":[a.model_dump(mode="json") for a in answers],"phase":phase},Evaluation,"evaluate")
    if not isinstance(candidate, Evaluation):
        raise ReviewFailure("structured_parse", "invalid_evaluation_structure", phase)
    result = Evaluation(intent_version=intent.version,phase=phase,assessments=[],diagnostics=list(candidate.diagnostics))
    def note(code, req=None):
        result.diagnostics.append(FailureDiagnostic(failure_layer="semantic_validation",stage=phase,
            validation_code=code,requirement_id=req))
    if candidate.phase != phase or candidate.intent_version != intent.version:
        # A non-wire/custom provider may still return these fields. Wrong binding
        # cannot be safely assumed to describe this operation.
        for requirement in intent.requirements:
            note("assessment_binding_mismatch", requirement.requirement_id)
            result.assessments.append(uncertain(requirement.model_dump(),"The assessment could not be tied reliably to the current request. Review is needed."))
        return result
    unknown = set(a.requirement_id for a in candidate.assessments)-set(ids)
    if unknown: note("unknown_requirement_mapping")
    if candidate.assessments and not any(a.requirement_id in ids for a in candidate.assessments):
        raise ReviewFailure("semantic_validation", "unmappable_assessment_response", phase)
    source = {a.response_id:a.text for a in answers}
    def valid(e): return bool(e.excerpt.strip()) and e.excerpt in source.get(e.response_id, "")
    for requirement in intent.requirements:
        matching = [a for a in candidate.assessments if a.requirement_id==requirement.requirement_id]
        if len(matching) != 1:
            note("missing_assessment" if not matching else "duplicate_assessment",requirement.requirement_id)
            result.assessments.append(uncertain(requirement.model_dump(),"A unique assessment was not available for this requirement. Review is needed."))
            continue
        item = matching[0].model_copy(deep=True)
        if item.requirement_text != requirement.text: note("canonical_text_restored",requirement.requirement_id)
        item.requirement_text = requirement.text
        defects = []
        if not item.explanation.strip(): defects.append("missing_assessment_explanation")
        if any(not valid(e) for e in item.evidence): defects.append("invalid_evidence")
        item.evidence = [e for e in item.evidence if valid(e)]
        accepted_conflicts = []
        for finding in item.consistency_findings:
            supported = (finding.certainty in {"confirmed","uncertain"} and finding.explanation.strip()
                         and all(valid(e) for e in finding.evidence))
            if finding.certainty == "confirmed":
                supported = supported and len({(e.response_id,e.excerpt) for e in finding.evidence}) >= 2
            if not supported:
                defects.append("unsupported_contradiction")
                continue
            accepted_conflicts.append(finding)
            item.evidence.extend(e for e in finding.evidence if e not in item.evidence)
        item.consistency_findings = accepted_conflicts
        confirmed = [f for f in accepted_conflicts if f.certainty=="confirmed"]
        ambiguous = [f for f in accepted_conflicts if f.certainty=="uncertain"]
        if confirmed:
            item.status=Status.partial
            item.explanation=" ".join(f.explanation for f in confirmed)
        elif ambiguous:
            item.status=Status.needs_review
            item.uncertainty_reason=" ".join(f.explanation for f in ambiguous)
        if item.status==Status.complete and not item.evidence: defects.append("complete_without_evidence")
        if item.status==Status.needs_review and not (item.uncertainty_reason or "").strip(): defects.append("missing_uncertainty_reason")
        if defects:
            for code in sorted(set(defects)): note(code,requirement.requirement_id)
            item.status=Status.needs_review
            item.explanation="PickyLens could not validate this assessment reliably. Inspect the available evidence before resolving it."
            item.uncertainty_reason="The generated assessment contained unsupported evidence or incomplete justification."
        result.assessments.append(item)
    return result
