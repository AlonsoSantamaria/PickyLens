"""Host-neutral review of submitted text and externally produced answers."""
import asyncio
from app.core import pre, evaluation
from app.core import next as next_stage
from app.core.contracts import ApprovedIntent, Answer, Snapshot, uid
from app.providers.telemetry import calls
from app.core.failures import failure_diagnostic


class HostReview:
    def __init__(self, repository, provider, timeout=45):
        self.repo, self.provider, self.timeout = repository, provider, timeout

    async def _run(self, snapshot, action, operation, perform):
        snapshot.pending_operation, snapshot.pending_action = operation, action
        snapshot.stage = action
        snapshot.failure = None
        snapshot = self.repo.save(snapshot, action + "_started", operation,
                                  snapshot.revision or None, claim=True, signature=action)
        bucket = []
        token = calls.set(bucket)
        try:
            await asyncio.wait_for(perform(snapshot), timeout=self.timeout)
            review = snapshot.post if action == "post" else None
            if review:
                for diagnostic in review.diagnostics:
                    if bucket: diagnostic.call_id, diagnostic.response_id = bucket[-1].call_id, bucket[-1].response_id
                    snapshot.diagnostics.append(diagnostic.model_copy(deep=True))
            snapshot.failed_action = None
            event = action + "_completed"
        except (Exception, asyncio.CancelledError) as exc:
            snapshot.diagnostics.append(failure_diagnostic(exc,action,bucket))
            snapshot.failure = "Review unavailable. Saved work is preserved; retry manually."
            snapshot.failed_action = action
            snapshot.lifecycle_status = "Review unavailable"
            event = action + "_failed"
        finally:
            calls.reset(token)
            for entry in bucket:
                entry.operation_id = operation
            snapshot.model_calls.extend(bucket)
        return self.repo.finish(snapshot, operation, event)

    async def request(self, text, interaction_id=None):
        snapshot = Snapshot(interaction_id=interaction_id or uid(), original_request=text,
                            current_request=text, title="External host text review",
                            test_stub=self.provider.test_stub)
        async def perform(s):
            if not text.strip():
                raise ValueError("Empty request")
            s.pre = await pre.review(self.provider, text)
            # Submission authorizes the original text, never the proposed rewrite.
            s.intent = ApprovedIntent(version=1, original_request=text, approved_prompt=text,
                approval_action="host_submitted_request; extraction_not_user_confirmed",
                accepted_clarifications={}, requirements=s.pre.requirements)
            s.selected_prompt = text
            s.stage, s.lifecycle_status = "ai", "Awaiting host answer"
        return await self._run(snapshot, "pre", uid(), perform)

    async def answer(self, interaction_id, text):
        snapshot = self.repo.get(interaction_id)
        if snapshot.pending_operation or snapshot.answer is not None:
            return snapshot
        snapshot.answer = Answer(text=text, metadata={"origin": "external_host"})
        # Persist the external evidence even if request review failed.
        snapshot = self.repo.save(snapshot, "external_answer_received", uid(), snapshot.revision)
        if not snapshot.intent or not snapshot.intent.requirements:
            snapshot.failure = "Answer saved, but no usable request review is available. Review manually."
            snapshot.lifecycle_status = "Review unavailable"
            return self.repo.save(snapshot, "post_unavailable", uid(), snapshot.revision)
        async def perform(s):
            if not text.strip():
                raise ValueError("No host answer")
            s.post = await evaluation.evaluate(self.provider, s.intent, [s.answer], "post")
            s.stage = "post"
            s.lifecycle_status = ("Complete after first response" if all(
                a.status == "complete" for a in s.post.assessments) else "Review findings available")
        return await self._run(snapshot, "post", uid(), perform)

    async def repair(self, interaction_id, approved_uncertainty=()):
        snapshot = self.repo.get(interaction_id)
        if snapshot.pending_operation or not snapshot.post or not snapshot.answer:
            raise ValueError("A completed answer review is required")
        if snapshot.next:
            return snapshot
        allowed = {a.requirement_id for a in snapshot.post.assessments if a.status in {"partial", "missing"}}
        uncertain = {a.requirement_id for a in snapshot.post.assessments if a.status == "needs_review"}
        if not set(approved_uncertainty) <= uncertain or not (allowed | set(approved_uncertainty)):
            raise ValueError("No approved repair targets")
        snapshot.approved_uncertainty = list(approved_uncertainty)
        async def perform(s):
            s.next = await next_stage.generate(self.provider, s.intent, s.post, s.answer,
                                               approved_uncertainty)
            s.followup_draft = s.next.text
            s.stage, s.lifecycle_status = "next", "Repair draft; not sent"
        return await self._run(snapshot, "next", uid(), perform)
