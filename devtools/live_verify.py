"""Bounded initial capture: PRE, one answer, POST. Never retries automatically."""
import asyncio
import json
from pathlib import Path
from app.config import load_settings
from app.providers.openai_adapter import OpenAIProvider
from app.core.contracts import now, ApprovedIntent, Requirement
from app.core.pre import review
from app.core.evaluation import evaluate
from app.services.scenario import PROMPT, REQUIREMENTS

DEST = Path("work/live-verification")


class Recorder:
    def __init__(self):
        DEST.mkdir(parents=True, exist_ok=True)
        self.path = DEST / "calls.json"
        self.records = json.loads(self.path.read_text()) if self.path.exists() else []

    def save(self):
        self.path.write_text(json.dumps(self.records, indent=2), encoding="utf-8")

    def begin(self, purpose, args):
        if len(self.records) >= 8:
            raise ValueError("Authorized eight-call limit reached")
        r = {"call_number":len(self.records)+1, "purpose":purpose, "started_at":now(),
             "requested_model":args["model"], "reasoning":args["reasoning"], "request":args["input"], "status":"attempted"}
        self.records.append(r)
        self.save()
        print(f"Call {r['call_number']}: {purpose}; model={args['model']}", flush=True)
        return r

    def fail(self, r, error_type, status, code):
        r.update(status="failed", error_type=error_type, http_status=status, error_code=code, completed_at=now())
        self.save()

    def finish(self, r, response):
        r.update(status=response.status, completed_at=now(), response_id=response.id, returned_model=response.model,
                 usage=response.usage.model_dump() if response.usage else None)
        self.save()
        (DEST / f"response-{r['call_number']}.json").write_text(response.model_dump_json(indent=2), encoding="utf-8")


async def main():
    settings = load_settings()
    print("Local configuration loaded; API key present:", bool(settings.api_key.get_secret_value()), flush=True)
    if settings.model != "gpt-5.6-sol" or settings.reasoning_effort != "low":
        raise ValueError("Configured model/effort differs from approved verification; decision required")
    recorder = Recorder()
    if recorder.records:
        raise ValueError("Existing call ledger found; inspect before any further capture")
    provider = OpenAIProvider(settings, recorder)
    try:
        proposal = await review(provider, PROMPT)
        (DEST / "pre.json").write_text(proposal.model_dump_json(indent=2), encoding="utf-8")
        intent = ApprovedIntent(version=1, original_request=PROMPT, approved_prompt=PROMPT,
            approval_action="authorized_original_scenario_verification", accepted_clarifications={},
            requirements=[Requirement(text=text) for text in REQUIREMENTS])
        (DEST / "intent.json").write_text(intent.model_dump_json(indent=2), encoding="utf-8")
        answer = await provider.generate_text({"prompt":PROMPT}, "answer")
        (DEST / "answer.json").write_text(answer.model_dump_json(indent=2), encoding="utf-8")
        result = await evaluate(provider, intent, [answer], "post")
        (DEST / "post.json").write_text(result.model_dump_json(indent=2), encoding="utf-8")
        print("POST counts:", result.counts(), flush=True)
        print("Initial capture finished. Inspect evidence before follow-up or fixture publication.", flush=True)
    finally:
        await provider.client.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except ValueError as exc:
        print(str(exc))
        raise SystemExit(1)
