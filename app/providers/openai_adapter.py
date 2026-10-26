import json
import logging
from time import perf_counter
from types import SimpleNamespace
from pydantic import ValidationError
from openai import AsyncOpenAI
# Pinned SDK schema conversion is retained; local parsing uses public Pydantic APIs.
from openai.lib._parsing._responses import type_to_text_format_param
from app.core.contracts import ModelCall, Answer
from app.core.failures import ReviewFailure, failure_diagnostic, validation_diagnostics
from app.core.model_contracts import wire_contract
from app.providers.telemetry import calls

logger = logging.getLogger(__name__)

INSTRUCTIONS = {
 "pre": "Review the request for material ambiguity, contradictions, and missing human decisions. Do not invent decisions. Extract only explicitly requested requirements. Readiness is green, amber, or red. Suggest concise improvements; keep unresolved decisions as questions. Requirements are plain strings; do not generate requirement identifiers or source metadata. Clarifications contain questions, options and required flags; no keys. Return the requested schema.",
 "evaluate": "Fill each fixed requirement slot with its judgment. Do not produce requirement IDs, requirement text, intent versions or phases. Use complete, partial, missing, or needs_review. Do not invent omissions or evidence. Evidence excerpts must be exact contiguous quotations from the supplied answer with its answer_index. Explain uncertainty. Evaluate all supplied answers together. Inspect internal consistency across sections, including quantities, arithmetic, timelines, recommendations, and conditions relevant to each requirement. Presence alone is insufficient for Complete. Report unresolved material contradictions in consistency_findings: certainty confirmed with exact excerpts of BOTH conflicting claims, or uncertain when scope/time/definitions leave insufficient evidence. Use Partial for addressed but materially inconsistent or unreliable requirements and Needs review for unproven apparent conflicts. A footnote that contradicts a still-present executive summary or table does not make the delivered memo consistently reliable. During VERIFY, an explicit follow-up correction may resolve an earlier conflict if it clearly supersedes the erroneous claims; do not keep resolved conflicts open. Never invent defects. Return the requested schema.",
 "next": "Write the smallest useful follow-up addressing only allowed_targets. For material inconsistency, request only the corrected figures or claims and explicit replacement of the conflicting statements. Do not repeat completed work. Address all and only the allowed targets. Return only the follow-up text. Return the requested schema."
}


class OpenAIProvider:
    test_stub = False

    def __init__(self, settings, recorder=None):
        if settings.provider != "openai" or not settings.api_key.get_secret_value():
            raise ValueError("OpenAI configuration is missing or unsupported")
        self.settings = settings
        self.client = AsyncOpenAI(api_key=settings.api_key.get_secret_value(), max_retries=0, timeout=settings.timeout)
        self.recorder = recorder

    async def request(self, messages, purpose, schema=None, decoder=None):
        args = dict(model=self.settings.model, reasoning={"effort": self.settings.reasoning_effort}, input=messages, store=False, max_output_tokens=6000)
        envelope = json.dumps({'messages': messages, 'schema': schema.model_json_schema() if schema else None})
        if len(envelope.encode('utf-8')) > 260000:
            raise ReviewFailure("access", "request_size_limit", purpose)
        record = self.recorder.begin(purpose, args) if self.recorder else None
        entry = ModelCall(provider="openai", model=self.settings.model, purpose=purpose)
        bucket = calls.get()
        if bucket is not None: bucket.append(entry)
        started = perf_counter()
        def fail(layer, code, error_type):
            entry.status, entry.error_type = "failed", error_type
            error = ReviewFailure(layer, code, purpose)
            diagnostic = failure_diagnostic(error, purpose, [entry])
            entry.diagnostics.append(diagnostic)
            logger.warning("PickyLens failure: %s", diagnostic.model_dump_json())
            return error
        try:
            if schema: args['text'] = {"format":type_to_text_format_param(schema)}
            response = await self.client.responses.create(**args)
        except Exception as exc:
            status = getattr(exc,"status_code",None)
            code = {401:"provider_authentication",403:"provider_permission",429:"provider_quota_or_rate_limit"}.get(status)
            if code is None:
                code = {"APITimeoutError":"provider_timeout", "APIConnectionError":"provider_network",
                        "ValidationError":"provider_envelope_invalid"}.get(type(exc).__name__,"provider_request_failed")
            if isinstance(exc, ValidationError):
                from openai.types.responses import Response
                for detail in validation_diagnostics(exc,Response,purpose,"provider_envelope"):
                    detail.call_id=entry.call_id
                    entry.diagnostics.append(detail)
            if record is not None: self.recorder.fail(record,type(exc).__name__,status,None)
            raise fail("provider_envelope",code,type(exc).__name__) from None
        finally:
            entry.duration_ms = round((perf_counter()-started)*1000,2)
        entry.status,entry.response_id,entry.model = response.status,response.id,response.model
        if response.usage:
            entry.input_tokens,entry.output_tokens,entry.total_tokens = response.usage.input_tokens,response.usage.output_tokens,response.usage.total_tokens
            entry.reasoning_tokens = getattr(getattr(response.usage,"output_tokens_details",None),"reasoning_tokens",None)
        if record is not None: self.recorder.finish(record,response)
        if response.status != "completed":
            raise fail("provider_envelope","provider_incomplete","IncompleteResponse")
        if schema:
            # Ignore non-final commentary. Never turn a refusal into a judgment.
            parts = [part for output in (response.output or []) if output.type == "message"
                     and getattr(output,"phase",None) in {None,"final_answer"} for part in (output.content or [])]
            if any(part.type == "refusal" for part in parts):
                raise fail("structured_parse","provider_refusal","MissingStructuredResult")
            texts = [part.text for part in parts if part.type == "output_text"]
            if len(texts) != 1 or not texts[0].strip():
                raise fail("structured_parse","missing_or_ambiguous_structured_result","MissingStructuredResult")
            try:
                parsed = (decoder or schema.model_validate_json)(texts[0])
            except ReviewFailure as exc:
                raise fail(exc.diagnostic.failure_layer,exc.diagnostic.validation_code,"InvalidStructuredResult") from None
            except ValidationError as exc:
                for detail in validation_diagnostics(exc,schema,purpose):
                    detail.call_id,detail.response_id=entry.call_id,entry.response_id
                    entry.diagnostics.append(detail)
                raise fail("structured_parse","structured_schema_invalid","ValidationError") from None
            # Diagnostics contain only application-owned codes/identifiers, no raw values.
            for diagnostic in getattr(parsed,"diagnostics",[]):
                diagnostic.response_id,diagnostic.call_id = entry.response_id,entry.call_id
            return SimpleNamespace(output_parsed=parsed)
        return response

    async def generate_structured(self, context, result_schema, purpose):
        model_context, wire_schema, decoder = wire_contract(context,result_schema,purpose)
        response = await self.request([{"role":"system","content":INSTRUCTIONS[purpose]},
            {"role":"user","content":json.dumps(model_context)}],context.get("phase",purpose),wire_schema,decoder)
        return response.output_parsed

    async def generate_text(self, context, purpose):
        messages = [{"role":"user","content":context["prompt"]}]
        if purpose == "followup":
            messages += [{"role":"assistant","content":context["first_answer"]},{"role":"user","content":context["followup"]}]
        response = await self.request(messages,purpose)
        if not response.output_text.strip():
            raise ReviewFailure("structured_parse","empty_answer",purpose)
        return Answer(text=response.output_text,metadata={"provider":"openai","model":response.model,
            "provider_response_id":response.id,"purpose":purpose})
