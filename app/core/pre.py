from app.core.contracts import PREProposal, uid
from app.core.failures import ReviewFailure


async def review(provider, request):
    result = await provider.generate_structured({"request":request},PREProposal,"pre")
    if not isinstance(result, PREProposal):
        raise ReviewFailure("structured_parse","invalid_pre_structure","pre")
    if result.readiness not in {"green","amber","red"} or (not result.requirements and result.readiness!="red"):
        raise ReviewFailure("semantic_validation","unusable_pre_requirements","pre")
    if any(not r.text.strip() for r in result.requirements):
        raise ReviewFailure("semantic_validation","blank_pre_requirement","pre")
    keys=[c.key for c in result.clarifications]
    if len(keys)!=len(set(keys)) or any(not c.key.strip() or not c.question.strip() for c in result.clarifications):
        raise ReviewFailure("semantic_validation","ambiguous_pre_clarifications","pre")
    if not result.improved_prompt.strip():
        raise ReviewFailure("semantic_validation","empty_improved_prompt","pre")
    for item in result.requirements:
        item.requirement_id=uid()
        item.source="original_request"
    return result
