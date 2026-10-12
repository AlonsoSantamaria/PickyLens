import hashlib
import json
import sqlite3
from app.core import pre, intent, evaluation
from app.core.next import generate
from app.core.contracts import Snapshot, Status, ApprovedIntent, Requirement
from app.services.replay import load_fixture, acquire
from app.storage.repository import Conflict
from app.providers.telemetry import calls


class StageFailure(ValueError):
    def __init__(self, snapshot, status_code=502):
        super().__init__(snapshot.failure)
        self.snapshot = snapshot
        self.status_code = status_code


def signature(name, action):
    return hashlib.sha256(json.dumps({"action": name, "input": action.model_dump(mode="json")}, sort_keys=True).encode()).hexdigest()


def clear_downstream(s):
    s.answer = s.post = s.next = s.followup_answer = s.verification = None
    s.followup_draft = None
    s.approved_uncertainty = []
    s.uncertainty_checked = []


def cancel_pending(s):
    s.pending_operation = s.pending_action = None
    s.failure = s.failed_action = None
    s.lifecycle_status = "In progress"


class Interactions:
    def __init__(self, repository, provider):
        self.repository, self.provider = repository, provider

    def claim(self, s, event, action, sig):
        try:
            return self.repository.save(s, event, action.operation_id, s.revision if s.revision else None, claim=True, signature=sig)
        except sqlite3.IntegrityError:
            raise Conflict("Operation already claimed. Reload or redeliver the same operation.") from None

    async def start(self, action):
        sig = signature("start", action)
        duplicate = self.repository.duplicate(action.operation_id, sig)
        if duplicate:
            return duplicate
        request = load_fixture()["prompt"].strip() if action.canonical_scenario else (action.request_text or "").strip()
        if not request:
            raise ValueError("Enter a request to begin.")
        if action.mode not in {"live", "replay"}:
            raise ValueError("Invalid interaction mode.")
        s = Snapshot(original_request=request, current_request=request, mode=action.mode,
            test_stub=self.provider.test_stub, canonical_ready=action.canonical_scenario,
            pending_operation=action.operation_id, pending_action="pre")
        try:
            s = self.claim(s, "interaction_started", action, sig)
        except Conflict:
            duplicate = self.repository.duplicate(action.operation_id, sig)
            if duplicate:
                return duplicate
            raise
        return await self.run(s, "pre", action)

    async def act(self, id, name, a):
        try:
            return await self._act(id, name, a)
        except Conflict:
            duplicate = self.repository.duplicate(a.operation_id, signature(name, a), id)
            if duplicate:
                return duplicate
            raise

    async def _act(self, id, name, a):
        sig = signature(name, a)
        duplicate = self.repository.duplicate(a.operation_id, sig, id)
        if duplicate:
            return duplicate
        s = self.repository.get(id)
        if s.terminal:
            raise Conflict("Completed interactions are read-only.")
        if a.expected_revision != s.revision:
            raise Conflict("The saved interaction changed. Reload before continuing.")
        if s.pending_operation and name not in {"pause", "request", "reset-scenario", "mode"}:
            raise Conflict("An operation is still in progress.")
        if s.lifecycle_status == "Paused" and name != "resume":
            raise Conflict("Resume the interaction before continuing.")
        if name == "pause":
            if s.pending_action:
                s.failed_action = s.pending_action
                s.failure = "Operation paused before completion. Retry explicitly after resuming."
            s.pending_operation = s.pending_action = None
            s.lifecycle_status = "Paused"
            return self.claim(s, "interaction_paused", a, sig)
        if name == "resume":
            s.lifecycle_status = "Incomplete" if s.failure else "In progress"
            return self.claim(s, "interaction_resumed", a, sig)
        if name in {"request", "reset-scenario"}:
            text = load_fixture()["prompt"].strip() if name == "reset-scenario" else (a.request_text or "").strip()
            if not text:
                raise ValueError("Enter a request to begin.")
            cancel_pending(s)
            clear_downstream(s)
            s.current_request = text
            s.pre = s.intent = s.selected_prompt = None
            s.accepted_clarifications = {}
            s.canonical_ready = name == "reset-scenario"
            if s.canonical_ready:
                s.mode = "replay"
            s.stage = "pre"
            s.pending_operation, s.pending_action = a.operation_id, "pre"
            s = self.claim(s, "scenario_reset" if s.canonical_ready else "request_changed", a, sig)
            return await self.run(s, "pre", a)
        if name == "mode":
            if a.mode not in {"live", "replay"}:
                raise ValueError("Invalid mode")
            if a.mode == s.mode:
                return self.claim(s, "mode_unchanged", a, sig)
            if (s.answer or s.pending_operation) and not a.confirmed_switch:
                raise ValueError("Confirm superseding the current response and reviews")
            if a.mode == "replay" and s.intent:
                acquire(s.intent)
            pending_pre = s.pending_action == "pre"
            had_response = bool(s.answer)
            cancel_pending(s)
            if pending_pre:
                s.failed_action = "pre"
                s.failure = "PRE was interrupted. Retry the review."
            s.mode = a.mode
            if had_response:
                clear_downstream(s)
                s.stage = "ai"
            return self.claim(s, "mode_changed", a, sig)
        if name == "clarifications":
            if s.stage != "pre" or not s.pre:
                raise ValueError("Run PRE first")
            allowed = {c.key: c for c in s.pre.clarifications}
            for key, value in a.clarifications.items():
                if key not in allowed or not value.strip() or (allowed[key].options and value not in allowed[key].options):
                    raise ValueError("Invalid clarification")
            s.accepted_clarifications = a.clarifications
            return self.claim(s, "clarification_accepted", a, sig)
        if name in {"approve-intent", "approve-canonical"}:
            if s.stage != "pre" or not s.pre or s.failure:
                raise ValueError("Complete PRE first")
            if name == "approve-canonical":
                if not s.canonical_ready:
                    raise ValueError("Reset to the canonical scenario and review first")
                if s.pre.readiness == "red" and not a.confirmed_red:
                    raise ValueError("Confirm sending despite PRE warning")
                f = load_fixture()
                s.intent = ApprovedIntent(version=s.revision, original_request=s.current_request,
                    approved_prompt=f["prompt"], approval_action="explicit_canonical_original", accepted_clarifications={},
                    replay_scenario=f["scenario_id"], replay_binding=f["canonical_intent"],
                    requirements=[Requirement(text=t, source=k) for k,t in zip(f["canonical_keys"],f["requirements"])])
            else:
                s.intent = intent.approve(s, a)
            s.selected_prompt = s.intent.approved_prompt
            s.stage = "ai"
            return self.claim(s, "intent_approved", a, sig)
        if name == "followup-draft":
            if s.stage != "next" or not s.next or not (a.prompt or "").strip():
                raise ValueError("A generated follow-up is required")
            s.followup_draft = a.prompt
            return self.claim(s, "followup_edited", a, sig)
        review = s.verification or s.post
        if name == "finish-review":
            if not review or s.stage not in {"post_reviewed", "verified"} or any(x.status in {Status.partial, Status.missing} for x in review.assessments):
                raise ValueError("Material repairable gaps remain")
            s.lifecycle_status = "Completed with review items"
            s.stage = "done"
            return self.claim(s, "interaction_completed", a, sig)
        if name == "approve-uncertainty":
            uncertain = {x.requirement_id for x in review.assessments if x.status == Status.needs_review} if review else set()
            if not a.requirement_ids or not set(a.requirement_ids) <= uncertain.intersection(s.uncertainty_checked):
                raise ValueError("Check the uncertainty against existing evidence first")
            s.approved_uncertainty = sorted(set(s.approved_uncertainty) | set(a.requirement_ids))
            return self.claim(s, "uncertainty_followup_approved", a, sig)
        if name == "retry":
            if not s.failed_action:
                raise ValueError("No failed operation to retry")
            name = s.failed_action
        elif s.failure and name != s.failed_action:
            raise ValueError("Retry the failed step or revise the request")
        required = {"pre": "pre", "answer": "ai", "post": "post", "next": "post_reviewed", "followup": "next", "verify": "verify", "resolve": "post_reviewed"}
        valid = s.stage == required.get(name) or (name == "resolve" and s.stage == "verified")
        if not valid or name not in required:
            raise ValueError("This action is not available at the current stage")
        if name == "resolve" and not any(x.status == Status.needs_review for x in review.assessments):
            raise ValueError("No uncertainty to resolve")
        if name == "next" and not s.approved_uncertainty and not any(x.status in {Status.partial, Status.missing} for x in review.assessments):
            raise ValueError("No repairable gaps were identified")
        if name == "answer" and s.mode == "replay":
            acquire(s.intent)
        s.pending_operation, s.pending_action = a.operation_id, name
        s = self.claim(s, "stage_started", a, sig)
        return await self.run(s, name, a)

    async def run(self, s, name, a):
        records = []
        token = calls.set(records)
        try:
            return await self._run(s, name, a, records)
        finally:
            calls.reset(token)

    async def _run(self, s, name, a, records):
        was_failure = bool(s.failure)
        before = s.model_copy(deep=True)
        try:
            if name == "pre":
                s.pre = await pre.review(self.provider, s.current_request)
                event = "pre_completed"
            elif name == "answer":
                s.answer = acquire(s.intent) if s.mode == "replay" else await self.provider.generate_text({"prompt": s.selected_prompt, "intent": s.intent.model_dump(mode="json")}, "answer")
                if not s.answer.text.strip():
                    raise ValueError("Empty answer")
                s.stage, event = "post", "response_received"
            elif name in {"post", "verify", "resolve"}:
                phase = "verify" if name == "verify" or (name == "resolve" and s.verification) else "post"
                answers = [s.answer] + ([s.followup_answer] if phase == "verify" else [])
                result = await evaluation.evaluate(self.provider, s.intent, answers, phase)
                if name == "resolve":
                    old = s.verification or s.post
                    uncertain = {x.requirement_id for x in old.assessments if x.status == Status.needs_review}
                    result.assessments = [x if x.requirement_id in uncertain else next(y for y in old.assessments if y.requirement_id == x.requirement_id) for x in result.assessments]
                    s.uncertainty_checked = sorted(uncertain)
                if phase == "post":
                    s.post, s.stage = result, "post_reviewed"
                else:
                    s.verification, s.stage = result, "verified"
                if all(x.status == Status.complete for x in result.assessments):
                    s.lifecycle_status = "Complete after verification" if phase == "verify" else "Complete after first response"
                    s.stage = "done"
                event = "uncertainty_resolved" if name == "resolve" else phase + "_completed"
            elif name == "next":
                s.next = await generate(self.provider, s.intent, s.post, s.answer, s.approved_uncertainty)
                s.followup_draft = s.next.text
                s.stage, event = "next", "next_generated"
            else:
                s.followup_answer = await self.provider.generate_text({"prompt": s.selected_prompt,
                    "first_answer": s.answer.text, "followup": s.followup_draft, "intent": s.intent.model_dump(mode="json")}, "followup")
                if not s.followup_answer.text.strip():
                    raise ValueError("Empty follow-up answer")
                s.stage, event = "verify", "followup_sent"
            s.failure = s.failed_action = None
            s.recovered = s.recovered or was_failure
            if not s.terminal:
                s.lifecycle_status = "Recovered after retry" if s.recovered else "In progress"
        except Exception as exc:
            status_code = 504 if isinstance(exc, TimeoutError) else 502
            s = before
            label = {"answer":"AI response", "followup":"Follow-up request", "resolve":"Uncertainty review"}.get(name, name.upper())
            s.failure = f"{label} could not be completed. Completed work is saved."
            s.failed_action = name
            s.lifecycle_status = "Failed at " + name.upper()
            self.attach_calls(s, records, a.operation_id)
            saved = self.repository.finish(s, a.operation_id, "stage_failed")
            if saved.failed_action == name and saved.failure:
                raise StageFailure(saved, status_code) from None
            return saved
        self.attach_calls(s, records, a.operation_id)
        return self.repository.finish(s, a.operation_id, event)

    @staticmethod
    def attach_calls(snapshot, records, operation_id):
        for record in records:
            record.operation_id = operation_id
        snapshot.model_calls.extend(records)
