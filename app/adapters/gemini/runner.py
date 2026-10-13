from app.adapters.gemini.protocol import HookInput, advisory
from app.adapters.gemini.presentation import render
from app.adapters.gemini.session_store import SessionStore


async def handle(payload, service):
    try:
        hook = HookInput.model_validate(payload)
    except Exception:
        return advisory("PickyLens review unavailable: invalid hook input. Gemini may continue unchanged.")
    store = SessionStore(service.repo)
    key, interaction, previous = store.reserve(hook)
    if previous:
        return advisory(previous)
    try:
        if hook.hook_event_name == "BeforeAgent":
            snapshot = await service.request(hook.prompt, interaction)
        else:
            text = "" if hook.prompt_response == "[no response text]" else hook.prompt_response
            snapshot = await service.answer(interaction, text)
        message = render(snapshot)
    except Exception:
        message = "PickyLens review unavailable. Completed work is preserved; use manual review."
    store.complete(key, message)
    return advisory(message)
