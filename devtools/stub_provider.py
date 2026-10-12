"""Deterministic test/development behavior, never a real model capture or Replay fixture."""
from app.core.contracts import PREProposal, Requirement, Finding, Clarification, Answer, Evaluation, Assessment, Evidence, Status, NextProposal
from app.services.scenario import REQUIREMENTS

FIRST = """EXECUTIVE SUMMARY
Choose Option A as a low-cost, fast way to reduce order errors while preserving operational continuity.

COMPARISON
Option A improves the existing manual process; Option B replaces it with integrated software.

COST
Option A costs $2,000 upfront and $200/month. Option B costs $8,000 upfront and $350/month.

IMPLEMENTATION TIME
Option A takes 2 weeks; Option B takes 6 weeks.

OPERATIONAL RISK
Option A retains transcription-error risk. Option B introduces migration disruption and staff-adoption risk.

RECOMMENDATION
Recommend Option A because it costs less, can be implemented sooner, and limits disruption. If the user prioritizes lowest upfront cost, this recommendation follows that priority.

ASSUMPTIONS AND UNCERTAINTIES
Assume the quoted costs are comparable and staff can attend training. Current error volume, demand growth, and actual software integration effort remain uncertain."""
FOLLOWUP = """QUESTIONS BEFORE ACTING
What is the current order-error rate and its financial cost? Can staff complete training within two weeks? Are there unlisted implementation costs? What demand growth would justify an integrated system?"""
EXCERPTS = [
    "Option A improves the existing manual process; Option B replaces it with integrated software.",
    "Option A costs $2,000 upfront and $200/month. Option B costs $8,000 upfront and $350/month.",
    "Option A takes 2 weeks; Option B takes 6 weeks.",
    "Option A retains transcription-error risk. Option B introduces migration disruption and staff-adoption risk.",
    "Recommend Option A because it costs less, can be implemented sooner, and limits disruption.",
    "Current error volume, demand growth, and actual software integration effort remain uncertain.",
    "What is the current order-error rate and its financial cost?",
    "Choose Option A as a low-cost, fast way to reduce order errors while preserving operational continuity.",
]


class StubProvider:
    test_stub = True

    def __init__(self):
        self.calls = []

    async def generate_text(self, context, purpose):
        self.calls.append(purpose)
        priority = context["intent"]["accepted_clarifications"].get("priority")
        first = FIRST + (f"\nPriority applied: {priority}." if priority else "")
        return Answer(text=FOLLOWUP if purpose == "followup" else first,
                      metadata={"provider": "deterministic-development-stub", "model": "none", "purpose": purpose})

    async def generate_structured(self, context, result_schema, purpose):
        self.calls.append(purpose)
        if purpose == "pre":
            result = PREProposal(readiness="amber", findings=[
                Finding(title="Missing priority", explanation="Should lowest upfront cost, speed, or operational risk dominate the recommendation?"),
                Finding(title="Redundant context", explanation="Packaging color and the founder's interests do not support this operational decision.")],
                clarifications=[Clarification(key="priority", question="Which priority should dominate?",
                    options=["Lowest upfront cost", "Implementation speed", "Operational risk"])],
                requirements=[Requirement(text=t) for t in REQUIREMENTS],
                improved_prompt=context["request"].replace("The business has used blue packaging for many years and the founder enjoys local history.", ""))
        elif purpose == "next":
            targets = context["allowed_targets"]
            result = NextProposal(text="Add only the key questions the owner should answer before acting. Do not repeat the memo.", target_requirement_ids=targets)
        else:
            intent = context["intent"]
            answers = context["answers"]
            assessments = []
            for i, req in enumerate(intent["requirements"]):
                excerpt = EXCERPTS[i] if i < len(EXCERPTS) else f"Priority applied: {intent["accepted_clarifications"].get("priority")}."
                match = next((a for a in answers if excerpt in a["text"]), None)
                assessments.append(Assessment(requirement_id=req["requirement_id"], requirement_text=req["text"],
                    status=Status.complete if match else Status.missing,
                    explanation="The answer includes supporting content." if match else "No key questions to answer before acting were found.",
                    evidence=[Evidence(response_id=match["response_id"], excerpt=excerpt, location="Named memo section")] if match else []))
            result = Evaluation(intent_version=intent["version"], phase=context["phase"], assessments=assessments)
        return result_schema.model_validate(result.model_dump())
