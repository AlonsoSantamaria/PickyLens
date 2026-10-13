"""Technical manual fallback and JSON hook entry point. No host inference calls."""
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from app.config import ROOT, load_settings
from app.adapters.gemini.runner import handle
from app.adapters.gemini.protocol import advisory
from app.adapters.gemini.presentation import render
from app.services.host_review import HostReview
from app.storage.repository import Repository


def repository():
    return Repository(os.environ.get("PICKYLENS_GEMINI_DB_PATH", str(ROOT / "data/gemini.sqlite3")))


class ConfiguredProvider:
    test_stub = False

    async def generate_structured(self, context, schema, purpose):
        # Delay configuration until the saved operation has begun, so failures persist.
        from app.providers.openai_adapter import OpenAIProvider
        settings = load_settings()
        settings.timeout = min(settings.timeout, 40)
        instance = OpenAIProvider(settings)
        try:
            return await instance.generate_structured(context, schema, purpose)
        finally:
            await instance.client.close()


async def main():
    parser = argparse.ArgumentParser(description="PickyLens technical Gemini fallback")
    parser.add_argument("action", choices=["hook", "review", "show", "draft-repair"])
    parser.add_argument("--interaction")
    parser.add_argument("--request-file", type=Path)
    parser.add_argument("--answer-file", type=Path)
    parser.add_argument("--approve-uncertainty", action="append", default=[])
    args = parser.parse_args()
    try:
        repo = repository()
        if args.action == "show":
            s = repo.get(args.interaction)
            print(render(s))
            print(s.model_dump_json(indent=2))
            return
        service = HostReview(repo, ConfiguredProvider())
        if args.action == "hook":
            raw = sys.stdin.read(1300001)
            if len(raw) > 1300000:
                raise ValueError("Input too large")
            result = await handle(json.loads(raw), service)
            print(json.dumps(result))
        elif args.action == "review":
            if not args.request_file:
                raise ValueError("Provide --request-file")
            s = await service.request(args.request_file.read_text(encoding="utf-8-sig"))
            if args.answer_file:
                s = await service.answer(s.interaction_id, args.answer_file.read_text(encoding="utf-8-sig"))
            print(render(s))
        else:
            s = await service.repair(args.interaction, args.approve_uncertainty)
            print(render(s))
    except Exception:
        message = "PickyLens review unavailable. Check local configuration or input; no retry was sent to Gemini."
        print(json.dumps(advisory(message)) if args.action == "hook" else message)
        if args.action != "hook":
            raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
