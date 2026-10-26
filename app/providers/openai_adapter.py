import json
import logging
from pydantic import ValidationError
from openai.lib._parsing._responses import type_to_text_format_param, parse_response

from time import perf_counter
from app.core.contracts import ModelCall
from app.providers.telemetry import calls
from openai import AsyncOpenAI
from app.core.contracts import Answer

logger = logging.getLogger(__name__)

INSTRUCTIONS = {
 "pre": "Review the request for material ambiguity, contradictions, and missing human decisions. Do not invent decisions. Extract only explicitly requested requirements. Readiness is green, amber, or red. Suggest concise improvements; keep unresolved decisions as questions. Requirement source is original_request. Return the requested schema.",
 "evaluate": "Assess every frozen requirement exactly once, preserving its ID and text verbatim. Use complete, partial, missing, or needs_review. Do not invent omissions or evidence. Evidence excerpts must be exact contiguous quotations from the supplied answer with its response_id. Explain uncertainty. Evaluate all supplied answers together. Inspect internal consistency across sections, including quantities, arithmetic, timelines, recommendations, and conditions relevant to each requirement. Presence alone is insufficient for Complete. Report unresolved material contradictions in consistency_findings: certainty confirmed with exact excerpts of BOTH conflicting claims, or uncertain when scope/time/definitions leave insufficient evidence. Use Partial for addressed but materially inconsistent or unreliable requirements and Needs review for unproven apparent conflicts. A footnote that contradicts a still-present executive summary or table does not make the delivered memo consistently reliable. During VERIFY, an explicit follow-up correction may resolve an earlier conflict if it clearly supersedes the erroneous claims; do not keep resolved conflicts open. Never invent defects. Preserve intent_version and phase. Return the requested schema.",
 "next": "Write the smallest useful follow-up addressing only allowed_targets. For material inconsistency, request only the corrected figures or claims and explicit replacement of the conflicting statements. Do not repeat completed work. Preserve target requirement IDs. Return the requested schema."
}


class OpenAIProvider:
    test_stub = False

    def __init__(self, settings, recorder=None):
        if settings.provider != "openai" or not settings.api_key.get_secret_value():
            raise ValueError("OpenAI configuration is missing or unsupported")
        self.settings = settings
        self.client = AsyncOpenAI(api_key=settings.api_key.get_secret_value(), max_retries=0, timeout=settings.timeout)
        self.recorder = recorder

    async def request(self, messages, purpose, schema=None):
        args = dict(model=self.settings.model, reasoning={"effort": self.settings.reasoning_effort}, input=messages, store=False, max_output_tokens=6000)
        # UTF-8 byte length is a conservative text-token bound. Leave ample headroom
        # for schema serialization and protocol overhead inside the 300k reservation.
        envelope = json.dumps({'messages': messages, 'schema': schema.model_json_schema() if schema else None})
        if len(envelope.encode('utf-8')) > 260000:
            raise ValueError("Request exceeds the bounded evaluation size.")
        record = self.recorder.begin(purpose, args) if self.recorder else None
        entry = ModelCall(provider="openai", model=self.settings.model, purpose=purpose)
        bucket = calls.get()
        if bucket is not None:
            bucket.append(entry)
        started = perf_counter()
        try:
            if schema:
                # Use the pinned SDK's identical strict schema, but retain the response
                # and usage before attempting local typed parsing.
                response = await self.client.responses.create(
                    **args, text={"format": type_to_text_format_param(schema)})
            else:
                response = await self.client.responses.create(**args)
        except Exception as exc:
            entry.status, entry.error_type = "failed", type(exc).__name__
            if isinstance(exc, ValidationError):
                # SDK response-envelope failures must also remain diagnosable.
                allowed = {"usage", "input_tokens_details", "output_tokens_details", "cached_tokens",
                           "cache_write_tokens", "reasoning_tokens", "output", "content", "text", "type",
                           "status", "id", "model", "phase", "input_tokens", "output_tokens", "total_tokens"}
                diagnostics = [{"type": e["type"], "path": [
                    part if isinstance(part, int) or part in allowed else "<field>"
                    for part in e["loc"]]} for e in exc.errors(include_input=False, include_context=False, include_url=False)]
                logger.warning("Provider envelope validation failed: purpose=%s errors=%s", purpose, json.dumps(diagnostics))
            if record is not None:
                self.recorder.fail(record, type(exc).__name__, getattr(exc, "status_code", None), getattr(exc, "code", None))
            raise ValueError(f"OpenAI request failed ({type(exc).__name__}, HTTP {getattr(exc, 'status_code', 'unavailable')}).") from None
        finally:
            entry.duration_ms = round((perf_counter() - started) * 1000, 2)
        entry.status, entry.response_id, entry.model = response.status, response.id, response.model
        if response.usage:
            entry.input_tokens = response.usage.input_tokens
            entry.output_tokens = response.usage.output_tokens
            entry.total_tokens = response.usage.total_tokens
            details = getattr(response.usage, "output_tokens_details", None)
            entry.reasoning_tokens = getattr(details, "reasoning_tokens", None)
        if record is not None:
            self.recorder.finish(record, response)
        if response.status != "completed":
            entry.error_type = "IncompleteResponse"
            logger.warning("Provider response incomplete: purpose=%s response_id=%s", purpose, response.id)
            raise ValueError("OpenAI response did not complete")
        if schema:
            try:
                response = parse_response(response=response, text_format=schema, input_tools=None)
                if response.output_parsed is None:
                    raise ValueError("OpenAI returned no structured result")
            except ValidationError as exc:
                entry.status, entry.error_type = "failed", "ValidationError"
                # Never log model text, input values, error context or arbitrary keys.
                definitions = schema.model_json_schema()
                allowed = set(definitions.get("properties", {}))
                for definition in definitions.get("$defs", {}).values():
                    allowed.update(definition.get("properties", {}))
                diagnostics = [{"type": e["type"], "path": [
                    part if isinstance(part, int) or part in allowed else "<field>"
                    for part in e["loc"]]} for e in exc.errors(include_input=False, include_context=False, include_url=False)]
                logger.warning("Structured response validation failed: purpose=%s response_id=%s errors=%s",
                               purpose, response.id, json.dumps(diagnostics))
                raise ValueError("OpenAI structured response failed validation") from None
            except ValueError:
                entry.status, entry.error_type = "failed", "MissingStructuredResult"
                raise
        return response

    async def generate_structured(self, context, result_schema, purpose):
        response = await self.request([{"role":"system", "content":INSTRUCTIONS[purpose]},
            {"role":"user", "content":json.dumps(context)}], context.get("phase", purpose), result_schema)
        if response.output_parsed is None:
            raise ValueError("OpenAI returned no structured result")
        return response.output_parsed

    async def generate_text(self, context, purpose):
        messages = [{"role":"user", "content":context["prompt"]}]
        if purpose == "followup":
            messages += [{"role":"assistant", "content":context["first_answer"]}, {"role":"user", "content":context["followup"]}]
        response = await self.request(messages, purpose)
        if not response.output_text.strip():
            raise ValueError("OpenAI returned an empty answer")
        return Answer(text=response.output_text, metadata={"provider":"openai", "model":response.model,
            "provider_response_id":response.id, "purpose":purpose})
