"""One explicitly authorized batch: two independent answers, each followed by POST."""
import asyncio
import json
from pathlib import Path
from app.config import load_settings
from app.core.contracts import ApprovedIntent
from app.core.evaluation import evaluate
from app.providers.openai_adapter import OpenAIProvider
from devtools.live_verify import Recorder, DEST


class BatchRecorder(Recorder):
    def begin(self, purpose, args):
        if len(self.records) >= 7:
            raise ValueError("Final batch limit reached: four additional calls")
        return super().begin(purpose, args)


async def main():
    settings = load_settings()
    if settings.model != "gpt-5.6-sol" or settings.reasoning_effort != "low":
        raise ValueError("Model/effort differs from the approved capture")
    recorder = BatchRecorder()
    if len(recorder.records) != 3:
        raise ValueError("Batch already started or ledger changed; no automatic rerun")
    intent = ApprovedIntent.model_validate_json((DEST / "intent.json").read_text(encoding="utf-8"))
    original = recorder.records[1]["request"]
    assert original == [{"role":"user", "content":intent.approved_prompt}]
    provider = OpenAIProvider(settings, recorder)
    try:
        for attempt in (1, 2):
            answer = await provider.generate_text({"prompt":intent.approved_prompt}, "answer")
            assert recorder.records[-1]["request"] == original
            (DEST / f"batch-answer-{attempt}.json").write_text(answer.model_dump_json(indent=2), encoding="utf-8")
            result = await evaluate(provider, intent, [answer], "post")
            (DEST / f"batch-post-{attempt}.json").write_text(result.model_dump_json(indent=2), encoding="utf-8")
            counts = result.counts()
            print(f"Attempt {attempt}: {counts}", flush=True)
            if counts["partial"] or counts["missing"]:
                print("Potential omission: stopped for manual evidence review. No further calls.", flush=True)
                break
    finally:
        await provider.client.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except ValueError as exc:
        print(str(exc))
        raise SystemExit(1)
