from app.core import pre, intent, evaluation
from app.core.next import generate
from app.core.contracts import Snapshot, Status, ApprovedIntent, Requirement
from app.services.replay import load_fixture, acquire
from app.storage.repository import Conflict


class Interactions:
    def __init__(self, repository, provider):
        self.repository, self.provider = repository, provider

    async def start(self, action):
        request = load_fixture()["prompt"].strip() if action.canonical_scenario else (action.request_text or "").strip()
        if not request:
            raise ValueError("Enter a request to begin.")
        if action.mode not in {"live", "replay"}:
            raise ValueError("Invalid interaction mode.")
        snapshot = Snapshot(original_request=request, current_request=request, mode=action.mode, test_stub=self.provider.test_stub, canonical_ready=action.canonical_scenario)
        snapshot = self.repository.save(snapshot, "interaction_started", action.operation_id, claim=True)
        return await self._review(snapshot, action)

    async def _review(self, s, a):
        try:
            s.pre = await pre.review(self.provider, s.current_request)
            return self.repository.save(s, "pre_completed", a.operation_id, s.revision)
        except Exception:
            s.failure = "PRE review could not be completed. Your request remains saved."
            s.lifecycle_status = "Failed at PRE"
            self.repository.save(s, "stage_failed", a.operation_id, s.revision)
            raise

    async def act(self, id, name, a):
        s = self.repository.get(id)
        if s.terminal:
            raise Conflict("Completed interactions are read-only.")
        if a.expected_revision != s.revision:
            raise Conflict("The saved interaction changed. Reload before continuing.")
        if name == "reset-scenario":
            s.mode = "replay"
            s.current_request = load_fixture()["prompt"].strip()
            s.pre = None
            s.intent = None
            s.selected_prompt = None
            s.accepted_clarifications = {}
            s.answer = s.post = s.next = s.followup_answer = s.verification = None
            s.followup_draft = None
            s.failure = None
            s.lifecycle_status = "In progress"
            s.canonical_ready = True
            s.stage = "pre"
            s = self.repository.save(s, "scenario_reset", a.operation_id, s.revision, claim=True)
            return await self._review(s, a)
        if name == "approve-canonical":
            if not s.canonical_ready or s.stage != "pre" or not s.pre:
                raise ValueError("Reset to the canonical scenario and review first")
            if s.pre.readiness == "red" and not a.confirmed_red:
                raise ValueError("Confirm sending despite PRE warning")
            f = load_fixture()
            s.intent = ApprovedIntent(version=s.revision, original_request=s.current_request,
                approved_prompt=f["prompt"], approval_action="explicit_canonical_original", accepted_clarifications={},
                replay_scenario=f["scenario_id"], replay_binding=f["canonical_intent"], requirements=[Requirement(text=t,source=k) for k,t in zip(f["canonical_keys"], f["requirements"])])
            s.selected_prompt = s.intent.approved_prompt
            s.stage = "ai"
            return self.repository.save(s,"intent_approved",a.operation_id,s.revision,claim=True)
        if name == "mode":
            if a.mode not in {"live","replay"}:
                raise ValueError("Invalid mode")
            if s.answer and not a.confirmed_switch:
                raise ValueError("Confirm superseding the current response and reviews")
            if a.mode == "replay" and s.intent:
                acquire(s.intent)
            s.mode = a.mode
            if s.answer:
                s.answer = s.post = s.next = s.followup_answer = s.verification = None
                s.followup_draft = None
                s.stage = "ai"
            return self.repository.save(s,"mode_changed",a.operation_id,s.revision,claim=True)
        if name == "clarifications":
            if s.stage != "pre" or not s.pre:
                raise ValueError("Run PRE first")
            allowed = {c.key: c for c in s.pre.clarifications}
            for key, value in a.clarifications.items():
                if key not in allowed or not value.strip():
                    raise ValueError("Invalid clarification")
                if allowed[key].options and value not in allowed[key].options:
                    raise ValueError("Choose a listed clarification")
            s.accepted_clarifications = a.clarifications
            return self.repository.save(s, "clarification_accepted", a.operation_id, s.revision, claim=True)
        if name == "approve-intent":
            if s.stage != "pre":
                raise ValueError("Intent can only be approved after PRE")
            s.intent = intent.approve(s, a)
            s.selected_prompt = s.intent.approved_prompt
            s.stage = "ai"
            return self.repository.save(s, "intent_approved", a.operation_id, s.revision, claim=True)
        if name == "followup-draft":
            if s.stage != "next" or not s.next or not (a.prompt or "").strip():
                raise ValueError("A generated follow-up is required")
            s.followup_draft = a.prompt
            return self.repository.save(s, "followup_edited", a.operation_id, s.revision, claim=True)
        required = {"answer": "ai", "post": "post", "next": "post_reviewed", "followup": "next", "verify": "verify"}
        if name not in required or s.stage != required[name]:
            raise ValueError("This action is not available at the current stage")
        if name == "next" and not any(x.status in {Status.partial, Status.missing} for x in s.post.assessments):
            raise ValueError("No repairable gaps were identified")
        s = self.repository.save(s, "stage_started", a.operation_id, s.revision, claim=True)
        if name == "answer":
            s.answer = acquire(s.intent) if s.mode == "replay" else await self.provider.generate_text({"prompt": s.selected_prompt, "intent": s.intent.model_dump(mode="json")}, "answer")
            if not s.answer.text.strip():
                raise ValueError("AI returned an empty answer")
            s.stage = "post"
            event = "response_received"
        elif name == "post":
            s.post = await evaluation.evaluate(self.provider, s.intent, [s.answer], "post")
            s.stage = "post_reviewed"
            if all(x.status == Status.complete for x in s.post.assessments):
                s.lifecycle_status = "Complete after first response"
                s.stage = "done"
            event = "post_completed"
        elif name == "next":
            s.next = await generate(self.provider, s.intent, s.post, s.answer)
            s.followup_draft = s.next.text
            s.stage = "next"
            event = "next_generated"
        elif name == "followup":
            s.followup_answer = await self.provider.generate_text({"prompt": s.selected_prompt,
                "first_answer": s.answer.text, "followup": s.followup_draft, "intent": s.intent.model_dump(mode="json")}, "followup")
            if not s.followup_answer.text.strip():
                raise ValueError("AI returned an empty follow-up answer")
            s.stage = "verify"
            event = "followup_sent"
        else:
            s.verification = await evaluation.evaluate(self.provider, s.intent, [s.answer, s.followup_answer], "verify")
            if all(x.status == Status.complete for x in s.verification.assessments):
                s.lifecycle_status = "Complete after verification"
                s.stage = "done"
            else:
                s.stage = "verified"
            event = "verify_completed"
        return self.repository.save(s, event, a.operation_id, s.revision)
