import asyncio
import sqlite3
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.core.contracts import Action, Status
from app.services.interactions import Interactions, StageFailure
from app.storage.repository import Repository, Conflict
from devtools.stub_provider import StubProvider
from app.services.scenario import PROMPT


def action(s=None, **extra):
    return Action(operation_id=str(uuid4()), expected_revision=s.revision if s else None, **extra)


async def approved(service):
    s=await service.start(action(request_text=PROMPT))
    return await service.act(s.interaction_id,"approve-intent",action(s,choice="original"))


class Flaky(StubProvider):
    broken=None
    async def generate_structured(self, context, schema, purpose):
        if self.broken == (context.get("phase") or purpose):
            raise RuntimeError("private provider diagnostics must not reach UI")
        return await super().generate_structured(context,schema,purpose)
    async def generate_text(self,context,purpose):
        if self.broken==purpose:
            raise RuntimeError("private provider diagnostics must not reach UI")
        return await super().generate_text(context,purpose)


@pytest.mark.parametrize("stage",["answer","post","next","followup","verify"])
def test_fail_retry_only_failed_step_preserves_context(tmp_path,stage):
    async def scenario():
        provider=Flaky();repo=Repository(tmp_path/"failure.sqlite3");svc=Interactions(repo,provider)
        s=await approved(svc)
        steps=["answer","post","next","followup","verify"]
        for step in steps[:steps.index(stage)]:s=await svc.act(s.interaction_id,step,action(s))
        before=s.model_copy(deep=True); calls=list(provider.calls)
        provider.broken=stage
        with pytest.raises(StageFailure):await svc.act(s.interaction_id,stage,action(s))
        failed=repo.get(s.interaction_id)
        assert failed.failed_action==stage and not failed.pending_operation
        assert "private" not in failed.failure
        for field in ["intent","answer","post","next","followup_draft","followup_answer","verification"]:
            assert getattr(failed,field)==getattr(before,field)
        assert failed.stage==before.stage
        provider.broken=None
        recovered=await svc.act(s.interaction_id,"retry",action(failed))
        assert recovered.recovered and not recovered.failure
        assert len(provider.calls)==len(calls)+1
    asyncio.run(scenario())


def test_duplicate_requests_and_conflicting_operation_ids(tmp_path):
    async def scenario():
        provider=StubProvider();repo=Repository(tmp_path/"duplicate.sqlite3");svc=Interactions(repo,provider)
        first=action(request_text=PROMPT)
        s=await svc.start(first)
        assert await svc.start(first)==s and provider.calls==["pre"]
        with pytest.raises(Conflict):await svc.start(first.model_copy(update={"request_text":"Different"}))
        approve=action(s,choice="original");s=await svc.act(s.interaction_id,"approve-intent",approve)
        answer=action(s);s=await svc.act(s.interaction_id,"answer",answer)
        events=len(repo.trace(s.interaction_id))
        assert await svc.act(s.interaction_id,"answer",answer)==s
        assert len(repo.trace(s.interaction_id))==events and provider.calls.count("answer")==1
        with pytest.raises(Conflict):await svc.act(s.interaction_id,"post",action(s.model_copy(update={"revision":1})))
    asyncio.run(scenario())


@pytest.mark.parametrize("change",["request","pause","mode"])
def test_late_response_is_trace_only_after_supersession(tmp_path,change):
    async def scenario():
        entered=asyncio.Event();release=asyncio.Event()
        class Slow(StubProvider):
            async def generate_text(self,context,purpose):
                entered.set();await release.wait()
                return await super().generate_text(context,purpose)
        provider=Slow();repo=Repository(tmp_path/"late.sqlite3");svc=Interactions(repo,provider)
        s=await svc.start(action(canonical_scenario=True))
        s=await svc.act(s.interaction_id,"approve-canonical",action(s))
        op=action(s);task=asyncio.create_task(svc.act(s.interaction_id,"answer",op));await entered.wait()
        pending=repo.get(s.interaction_id)
        duplicate=await svc.act(s.interaction_id,"answer",op)
        assert duplicate.pending_operation==op.operation_id
        changed=await svc.act(s.interaction_id,change,action(pending,request_text="New request",mode="replay",confirmed_switch=True))
        release.set();await task
        current=repo.get(s.interaction_id)
        assert current.answer is None
        assert current.current_request==changed.current_request and current.mode==changed.mode and current.lifecycle_status==changed.lifecycle_status
        events=repo.trace(s.interaction_id)
        assert events[-1]["type"]=="superseded_result" and events[-1]["superseded"].answer
        assert provider.calls.count("answer")==1
    asyncio.run(scenario())


def test_restart_pending_work_and_pause_resume(tmp_path):
    async def scenario():
        provider=StubProvider();db=tmp_path/"restart.sqlite3";repo=Repository(db);svc=Interactions(repo,provider)
        s=await approved(svc)
        s.pending_operation=str(uuid4());s.pending_action="answer"
        repo.save(s,"stage_started",s.pending_operation,s.revision,claim=True)
        restarted=create_app(provider,db);s=restarted.state.repository.get(s.interaction_id)
        assert s.lifecycle_status=="Interrupted" and s.failed_action=="answer" and s.answer is None
        assert provider.calls==["pre"]
        svc=Interactions(restarted.state.repository,provider)
        s=await svc.act(s.interaction_id,"pause",action(s));assert s.lifecycle_status=="Paused"
        with pytest.raises(Conflict):await svc.act(s.interaction_id,"retry",action(s))
        s=await svc.act(s.interaction_id,"resume",action(s))
        s=await svc.act(s.interaction_id,"retry",action(s))
        assert s.answer and s.recovered
    asyncio.run(scenario())


def test_request_edit_supersedes_intent_and_replay_binding(tmp_path):
    async def scenario():
        repo=Repository(tmp_path/"edit.sqlite3");svc=Interactions(repo,StubProvider())
        s=await approved(svc);old=s.intent
        s=await svc.act(s.interaction_id,"answer",action(s))
        s=await svc.act(s.interaction_id,"post",action(s))
        s=await svc.act(s.interaction_id,"request",action(s,request_text=PROMPT+" New constraint."))
        assert s.intent is None and s.answer is None and s.post is None and not s.canonical_ready
        s=await svc.act(s.interaction_id,"approve-intent",action(s,choice="original"))
        assert s.intent.version>old.version and s.intent.replay_binding is None
        assert any(e["snapshot"].intent==old for e in repo.trace(s.interaction_id))
    asyncio.run(scenario())


class Uncertain(StubProvider):
    async def generate_structured(self,context,schema,purpose):
        result=await super().generate_structured(context,schema,purpose)
        if purpose=="evaluate":
            for row in result.assessments:
                row.status=Status.needs_review;row.uncertainty_reason="Scope is unclear"
        return result


def test_uncertainty_requires_existing_evidence_check_and_explicit_approval(tmp_path):
    async def scenario():
        provider=Uncertain();repo=Repository(tmp_path/"uncertain.sqlite3");svc=Interactions(repo,provider)
        s=await approved(svc)
        for step in ["answer","post"]:s=await svc.act(s.interaction_id,step,action(s))
        assert not s.terminal
        with pytest.raises(ValueError):await svc.act(s.interaction_id,"next",action(s))
        target=s.post.assessments[0].requirement_id
        with pytest.raises(ValueError):await svc.act(s.interaction_id,"approve-uncertainty",action(s,requirement_ids=[target]))
        s=await svc.act(s.interaction_id,"resolve",action(s))
        assert provider.calls.count("answer")==1
        s=await svc.act(s.interaction_id,"approve-uncertainty",action(s,requirement_ids=[target]))
        s=await svc.act(s.interaction_id,"next",action(s))
        assert s.next.target_requirement_ids==[target] and s.followup_answer is None
    asyncio.run(scenario())


def test_qualified_terminal_is_immutable_and_nonresumable(tmp_path):
    async def scenario():
        db=tmp_path/"terminal.sqlite3";repo=Repository(db);svc=Interactions(repo,Uncertain())
        s=await approved(svc)
        for step in ["answer","post","finish-review"]:s=await svc.act(s.interaction_id,step,action(s))
        assert s.terminal and s.lifecycle_status=="Completed with review items"
        for step in ["resume","request","mode","retry","pause"]:
            with pytest.raises(Conflict):await svc.act(s.interaction_id,step,action(s))
        client=TestClient(create_app(StubProvider(),db))
        assert "Resume interaction" not in client.get(f"/interactions/{s.interaction_id}").text
        assert client.get(f"/?interaction={s.interaction_id}",follow_redirects=False).status_code==307
        with repo.connect() as connection:
            for query in ["DELETE FROM interaction_events", "UPDATE interaction_events SET event_type='changed'"]:
                with pytest.raises(sqlite3.IntegrityError):connection.execute(query)
    asyncio.run(scenario())


def test_red_requires_override_and_empty_input_does_not_start(tmp_path):
    async def scenario():
        class Red(StubProvider):
            async def generate_structured(self,context,schema,purpose):
                result=await super().generate_structured(context,schema,purpose)
                if purpose=="pre":result.readiness="red"
                return result
        repo=Repository(tmp_path/"red.sqlite3");svc=Interactions(repo,Red())
        with pytest.raises(ValueError):await svc.start(action(request_text="   "))
        assert repo.list()==[]
        s=await svc.start(action(request_text=PROMPT))
        with pytest.raises(ValueError):await svc.act(s.interaction_id,"approve-intent",action(s,choice="original"))
        s=await svc.act(s.interaction_id,"approve-intent",action(s,choice="original",confirmed_red=True))
        assert s.intent and s.selected_prompt==PROMPT.strip()
    asyncio.run(scenario())


def test_complete_first_answer_ends_without_next(tmp_path):
    async def scenario():
        class Complete(StubProvider):
            async def generate_text(self,context,purpose):
                from devtools.stub_provider import FOLLOWUP
                answer=await super().generate_text(context,purpose)
                answer.text+="\n"+FOLLOWUP
                return answer
        provider=Complete();repo=Repository(tmp_path/"complete.sqlite3");svc=Interactions(repo,provider)
        s=await approved(svc)
        for step in ["answer","post"]:s=await svc.act(s.interaction_id,step,action(s))
        assert s.lifecycle_status=="Complete after first response"
        with pytest.raises(Conflict):await svc.act(s.interaction_id,"next",action(s))
        assert provider.calls==["pre","answer","evaluate"]
    asyncio.run(scenario())


def test_late_post_does_not_replace_new_intent(tmp_path):
    async def scenario():
        entered=asyncio.Event();release=asyncio.Event()
        class Slow(StubProvider):
            async def generate_structured(self,context,schema,purpose):
                if purpose=="evaluate":entered.set();await release.wait()
                return await super().generate_structured(context,schema,purpose)
        repo=Repository(tmp_path/"late-post.sqlite3");svc=Interactions(repo,Slow())
        s=await approved(svc);s=await svc.act(s.interaction_id,"answer",action(s))
        task=asyncio.create_task(svc.act(s.interaction_id,"post",action(s)));await entered.wait()
        current=repo.get(s.interaction_id)
        current=await svc.act(s.interaction_id,"request",action(current,request_text=PROMPT+" Changed priority."))
        current=await svc.act(s.interaction_id,"approve-intent",action(current,choice="original"))
        release.set();await task
        saved=repo.get(s.interaction_id)
        assert saved.intent==current.intent and saved.post is None
        assert repo.trace(s.interaction_id)[-1]["superseded"].post
    asyncio.run(scenario())


def test_failure_and_stale_revision_http_include_saved_snapshot(tmp_path):
    provider=Flaky();provider.broken="pre";client=TestClient(create_app(provider,tmp_path/"http.sqlite3"))
    result=client.post("/api/interactions/pre",json=action(request_text=PROMPT).model_dump())
    assert result.status_code==502 and "private" not in result.text
    saved=result.json()["snapshot"]
    result=client.post(f"/api/interactions/{saved['interaction_id']}/retry",json={"operation_id":str(uuid4()),"expected_revision":0})
    assert result.status_code==409 and result.json()["snapshot"]==saved
