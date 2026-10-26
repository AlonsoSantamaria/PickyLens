"""Safe diagnostic codes, never exception text or model content."""
from app.core.contracts import FailureDiagnostic


class ReviewFailure(ValueError):
    def __init__(self, layer, code, stage, requirement_id=None):
        self.diagnostic = FailureDiagnostic(failure_layer=layer, validation_code=code,
                                            stage=stage, requirement_id=requirement_id)
        super().__init__(code)


def failure_diagnostic(exc, stage, records=()):
    if isinstance(exc, ReviewFailure):
        result = exc.diagnostic.model_copy(deep=True)
    else:
        from app.services.judge_access import AccessDenied
        result = FailureDiagnostic(failure_layer="access" if isinstance(exc, AccessDenied) else "semantic_validation",
            stage=stage, validation_code="allowance_denied" if isinstance(exc, AccessDenied) else "unexpected_stage_failure")
    if records:
        result.call_id = records[-1].call_id
        result.response_id = records[-1].response_id
    return result


def validation_diagnostics(exc, schema, stage, layer="structured_parse", requirement_id=None):
    definitions = schema.model_json_schema()
    allowed = set(definitions.get("properties", {}))
    for definition in definitions.get("$defs", {}).values():
        allowed.update(definition.get("properties", {}))
    return [FailureDiagnostic(failure_layer=layer, stage=stage, validation_code="schema_"+e["type"],
        requirement_id=requirement_id, field_path=[part if isinstance(part,int) or part in allowed else "<field>"
        for part in e["loc"]]) for e in exc.errors(include_input=False,include_context=False,include_url=False)]
