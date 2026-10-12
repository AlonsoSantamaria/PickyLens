import asyncio
from app.config import load_settings
from app.core.contracts import ApprovedIntent, Answer
from app.core.evaluation import evaluate
from app.providers.openai_adapter import OpenAIProvider
from devtools.live_verify import Recorder, DEST

async def main():
    recorder = Recorder()
    if len(recorder.records) != 7:
        raise ValueError("One-call reevaluation already used or unexpected ledger")
    settings = load_settings()
    if settings.model != "gpt-5.6-sol" or settings.reasoning_effort != "low":
        raise ValueError("Configured model differs from approved model")
    provider = OpenAIProvider(settings, recorder)
    try:
        intent = ApprovedIntent.model_validate_json((DEST / "intent.json").read_text(encoding="utf-8"))
        answer = Answer.model_validate_json((DEST / "batch-answer-1.json").read_text(encoding="utf-8"))
        result = await evaluate(provider, intent, [answer], "post")
        (DEST / "improved-post.json").write_text(result.model_dump_json(indent=2), encoding="utf-8")
        print(result.model_dump_json(indent=2))
    finally:
        await provider.client.close()

if __name__ == "__main__":
    asyncio.run(main())
