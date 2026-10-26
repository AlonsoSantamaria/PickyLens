import asyncio
import pytest
from app.core.contracts import ApprovedIntent, Requirement, Answer, Assessment, Evidence, Evaluation, ConsistencyFinding, Status
from app.core.evaluation import evaluate


@pytest.mark.parametrize("claims", [
    ("Total annual cost is 900.", "Total annual cost is 1200."),
    ("Deployment takes two weeks.", "Deployment takes nine weeks."),
    ("Offline access is supported.", "Internet access is required at all times."),
])
def test_confirmed_material_conflicts_are_partial_with_both_citations(claims):
    result = run_assessment(claims, "confirmed")
    assert result.status == Status.partial
    assert {e.excerpt for e in result.evidence} == set(claims)


def run_assessment(claims, certainty, fabricated=False):
    req = Requirement(text="Assess the proposed alternative reliably.")
    intent = ApprovedIntent(version=1, original_request=req.text, approved_prompt=req.text,
        approval_action="original", accepted_clarifications={}, requirements=[req])
    answer = Answer(text="\n".join(claims))
    evidence = [Evidence(response_id=answer.response_id, excerpt=c, location="Claim") for c in claims]
    if fabricated:
        evidence[0].excerpt = "This quotation does not exist."
    class Provider:
        async def generate_structured(self, context, schema, purpose):
            return Evaluation(intent_version=1, phase="post", assessments=[Assessment(
                requirement_id=req.requirement_id, requirement_text=req.text, status=Status.complete,
                explanation="Content present", evidence=[], consistency_findings=[ConsistencyFinding(
                    certainty=certainty, explanation="The claims use incompatible values for the same scope." if certainty=="confirmed" else "The time periods may differ; scope is unclear.", evidence=evidence)])])
    return asyncio.run(evaluate(Provider(), intent, [answer], "post")).assessments[0]


def test_apparent_conflict_with_unknown_scope_needs_review():
    item = run_assessment(("Estimate is 50.", "Actual is 80."), "uncertain")
    assert item.status == Status.needs_review and item.uncertainty_reason


def test_fabricated_conflict_evidence_is_rejected():
    result = run_assessment(("Cost is 30.", "Cost is 60."), "confirmed", True)
    assert result.status == Status.needs_review
    assert not result.consistency_findings
    assert all(e.excerpt != "This quotation does not exist." for e in result.evidence)


def test_confirmed_conflict_requires_two_distinct_claims():
    result = run_assessment(("Cost is 30.", "Cost is 30."), "confirmed")
    assert result.status == Status.needs_review and not result.consistency_findings
