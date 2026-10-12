from app.core.contracts import ApprovedIntent


def approve(snapshot, action):
    pre = snapshot.pre
    if not pre:
        raise ValueError("Review the request first")
    if action.choice not in {"original", "improved"}:
        raise ValueError("Choose original or improved prompt")
    if pre.readiness == "red" and action.choice == "original" and not action.confirmed_red:
        raise ValueError("Confirm Send original anyway")
    accepted = snapshot.accepted_clarifications if action.choice == "improved" else {}
    if action.choice == "improved" and any(c.required and not accepted.get(c.key) for c in pre.clarifications):
        raise ValueError("Resolve required clarifications first")
    prompt = snapshot.current_request if action.choice == "original" else pre.improved_prompt
    requirements = [r.model_copy(deep=True) for r in pre.requirements]
    from app.core.contracts import Requirement
    for key, value in accepted.items():
        requirements.append(Requirement(text=f"Accepted {key}: {value}", source="accepted_clarification"))
        prompt += f"\nAccepted {key}: {value}"
    return ApprovedIntent(version=1, original_request=snapshot.original_request, approved_prompt=prompt,
                          approval_action=action.choice, accepted_clarifications=accepted, requirements=requirements)
