from app.core.contracts import PREProposal, uid


async def review(provider, request):
    result = await provider.generate_structured({"request": request}, PREProposal, "pre")
    if result.readiness not in {"green", "amber", "red"} or not result.requirements:
        raise ValueError("Review did not establish usable requirements")
    for item in result.requirements:
        item.requirement_id = uid()
    return result
