"""Synthetic failure classes; not reproductions of unretained production outputs."""
import asyncio
import json
import sqlite3
from uuid import uuid4
import pytest
from openai import AuthenticationError, RateLimitError, APITimeoutError, APIConnectionError
import httpx
from app.config import load_settings
from app.core.contracts import (ApprovedIntent, Requirement, Answer, Evaluation, Assessment, Evidence,
    Status, Action, Snapshot, PREProposal, NextProposal)
from app.core.evaluation import evaluate
from app.core.next import generate
from app.core.model_contracts import wire_contract
from app.core.failures import ReviewFailure
from app.providers.openai_adapter import OpenAIProvider
from app.providers.telemetry import calls
from app.services.interactions import Interactions, StageFailure
from app.services.judge_access import JudgeAccess, BoundedProvider, principal
from app.storage.repository import Repository
from devtools.stub_provider import StubProvider
from tests.test_provider_validation import response


def inputs():
    intent=ApprovedIntent(version=7,original_request="Compare cost and timing.",approved_prompt="Compare cost and timing.",
        approval_action="original",accepted_clarifications={},requirements=[Requirement(text="Compare cost."),Requirement(text="Compare timing.")])
    answer=Answer(text="Cost is 20. Delivery takes two weeks.")
    context={"intent":intent.model_dump(mode="json"),"answers":[answer.model_dump(mode="json")],"phase":"post"}
    return intent,answer,context


def judgments():
    return {"r0":dict(status="complete",explanation="Cost stated",evidence=[dict(answer_index=0,excerpt="Cost is 20.",location="Cost")],uncertainty_reason=None,consistency_findings=[]),
            "r1":dict(status="complete",explanation="Time stated",evidence=[dict(answer_index=0,excerpt="Delivery takes two weeks.",location="Time")],uncertainty_reason=None,consistency_findings=[])}


@pytest.mark.parametrize("case",["valid","missing","duplicate","unknown","wrong_text","bad_status","bad_evidence","no_evidence","bad_answer_index","uncertain_no_reason","unsupported_conflict","ambiguous_conflict"])
def test_wire_and_semantic_defects_are_isolated(case):
    intent,answer,context=inputs(); raw=judgments()
    if case=="missing": del raw['r0']
    if case=="unknown": raw['unknown']=raw.pop('r0')
    if case=="wrong_text": raw['r0']['requirement_text']='INJECTED INTENT'
    if case=="bad_status": raw['r0']['status']='perfect'
    if case=="bad_evidence": raw['r0']['evidence'][0]['excerpt']='The cost amounts to 20.'
    if case=="no_evidence": raw['r0']['evidence']=[]
    if case=="bad_answer_index": raw['r0']['evidence'][0]['answer_index']=-1
    if case=="uncertain_no_reason": raw['r0']['status']='needs_review'
    if case in {'unsupported_conflict','ambiguous_conflict'}:
        raw['r0']['consistency_findings']=[dict(certainty='confirmed' if case=='unsupported_conflict' else 'uncertain',
            explanation='Scope is unclear.',evidence=raw['r0']['evidence'])]
    text=json.dumps(raw)
    if case=='duplicate': text=text[:-1]+',"r0":'+json.dumps(raw['r0'])+'}'
    model_context,schema,decode=wire_contract(context,Evaluation,'evaluate')
    assert 'intent_version' not in schema.model_fields and 'phase' not in schema.model_fields
    assert 'requirement_id' not in json.dumps(schema.model_json_schema())
    assert 'requirement_text' not in json.dumps(schema.model_json_schema())
    class Provider:
        async def generate_structured(self,*args): return decode(text)
    result=asyncio.run(evaluate(Provider(),intent,[answer],'post'))
    assert result.intent_version==7 and result.phase=='post'
    assert [a.requirement_id for a in result.assessments]==[r.requirement_id for r in intent.requirements]
    assert [a.requirement_text for a in result.assessments]==[r.text for r in intent.requirements]
    assert result.assessments[1].status==Status.complete
    assert result.assessments[0].status==(Status.complete if case=='valid' else Status.needs_review)
    assert all(e.excerpt in answer.text for a in result.assessments for e in a.evidence)
    if case=='unsupported_conflict': assert not result.assessments[0].consistency_findings


@pytest.mark.parametrize('text,code',[('[]','invalid_top_level'),('{','invalid_json'),('{"unknown":{}}','unmappable_assessment_response')])
def test_unusable_top_level_is_fatal(text,code):
    _,_,ctx=inputs(); _,_,decode=wire_contract(ctx,Evaluation,'evaluate')
    with pytest.raises(ReviewFailure) as err: decode(text)
    assert err.value.diagnostic.validation_code==code


@pytest.mark.parametrize('change',['phase','version','text','duplicate','missing','unknown'])
def test_custom_provider_cannot_change_canonical_intent(change):
    intent,answer,ctx=inputs(); _,_,decode=wire_contract(ctx,Evaluation,'evaluate'); result=decode(json.dumps(judgments()))
    if change=='phase': result.phase='verify'
    if change=='version': result.intent_version=90
    if change=='text': result.assessments[0].requirement_text='Changed by model'
    if change=='duplicate': result.assessments.append(result.assessments[0].model_copy(deep=True))
    if change=='missing': result.assessments.pop(0)
    if change=='unknown': result.assessments[0].requirement_id='unknown'
    class Provider:
        async def generate_structured(self,*args): return result
    normalized=asyncio.run(evaluate(Provider(),intent,[answer],'post'))
    assert normalized.intent_version==7 and normalized.phase=='post'
    assert normalized.assessments[0].requirement_text==intent.requirements[0].text
    if change=='text': assert normalized.assessments[0].status==Status.complete
    else: assert normalized.assessments[0].status==Status.needs_review
    if change not in {'phase','version'}: assert normalized.assessments[1].status==Status.complete
    else: assert all(a.status==Status.needs_review for a in normalized.assessments)
    assert normalized.diagnostics


def test_verify_can_use_followup_evidence_without_changing_ids():
    intent,answer,ctx=inputs(); followup=Answer(text='Correction: cost is 25, replacing the earlier 20.')
    ctx['answers'].append(followup.model_dump(mode='json'));ctx['phase']='verify'
    raw=judgments();raw['r0']['evidence']=[dict(answer_index=1,excerpt=followup.text,location='Correction')]
    _,_,decode=wire_contract(ctx,Evaluation,'evaluate')
    class Provider:
        async def generate_structured(self,*args):return decode(json.dumps(raw))
    result=asyncio.run(evaluate(Provider(),intent,[answer,followup],'verify'))
    assert all(a.status==Status.complete for a in result.assessments)
    assert result.assessments[0].evidence[0].response_id==followup.response_id
    assert result.assessments[0].requirement_id==intent.requirements[0].requirement_id


def test_pre_and_next_wire_identifiers_are_application_owned():
    _,schema,decode=wire_contract({'request':'Task'},PREProposal,'pre')
    result=decode(json.dumps(dict(readiness='green',findings=[],clarifications=[dict(question='Priority?',options=[],required=False)],requirements=['Compare costs'],improved_prompt='Compare costs')))
    assert result.requirements[0].source=='original_request' and result.requirements[0].requirement_id
    assert result.clarifications[0].key=='clarification_0'
    assert 'requirement_id' not in json.dumps(schema.model_json_schema())
    _,schema,decode=wire_contract({'allowed_targets':['canonical-1']},NextProposal,'next')
    assert set(schema.model_fields)=={'text'}
    assert decode('{"text":"Clarify cost only."}').target_requirement_ids==['canonical-1']


@pytest.mark.parametrize('kind',['auth','quota','timeout','network'])
def test_provider_failure_diagnostics_retry_and_settlement(tmp_path,kind):
    async def run():
        provider=OpenAIProvider(load_settings(tmp_path,{'OPENAI_API_KEY':'test-only'}))
        req=httpx.Request('POST','https://api.openai.com/v1/responses')
        exceptions={'auth':AuthenticationError('SECRET',response=httpx.Response(401,request=req),body=None),
            'quota':RateLimitError('SECRET',response=httpx.Response(429,request=req),body=None),
            'timeout':APITimeoutError(request=req),'network':APIConnectionError(request=req)}
        count=0
        async def fake(**kwargs):
            nonlocal count
            count+=1
            if count==1:raise exceptions[kind]
            return response(json.dumps(dict(readiness='green',findings=[],clarifications=[],requirements=['Compare costs'],improved_prompt='Compare costs')))
        provider.client.responses.create=fake
        access=JudgeAccess(tmp_path/'access.sqlite3');identity=access.validate(access.issue());token=principal.set(identity)
        repo=Repository(tmp_path/'interaction.sqlite3');svc=Interactions(repo,BoundedProvider(provider,access))
        action=Action(operation_id='start',request_text='Compare costs')
        try:
            with pytest.raises(StageFailure) as failure:await svc.start(action)
            s=repo.get(failure.value.snapshot.interaction_id)
            assert s.failed_action=='pre' and not s.pre and not s.pending_operation
            assert s.diagnostics[-1].failure_layer=='provider_envelope'
            assert s.diagnostics[-1].validation_code=={'auth':'provider_authentication','quota':'provider_quota_or_rate_limit','timeout':'provider_timeout','network':'provider_network'}[kind]
            assert 'SECRET' not in s.model_dump_json()
            await svc.start(action);assert count==1
            retry=Action(operation_id='retry',expected_revision=s.revision)
            recovered=await svc.act(s.interaction_id,'retry',retry)
            await svc.act(s.interaction_id,'retry',retry)
            assert count==2 and recovered.recovered and recovered.pre
            assert len(Repository(repo.path).get(s.interaction_id).model_calls)==2
            with access.connect() as db:assert [r[0] for r in db.execute('select tokens from reservations order by id')]==[300000,30]
        finally:principal.reset(token);await provider.client.close()
    asyncio.run(run())


@pytest.mark.parametrize('fatal',[False,True])
def test_semantic_outcome_preserves_usage_and_valid_work(tmp_path,fatal):
    async def run():
        intent,answer,ctx=inputs();provider=OpenAIProvider(load_settings(tmp_path,{'OPENAI_API_KEY':'test-only'}));count=0
        raw=judgments();raw['r0']['evidence'][0]['excerpt']='fabricated'
        async def fake(**kwargs):
            nonlocal count
            count+=1;return response('{"unknown":{}}' if fatal else json.dumps(raw))
        provider.client.responses.create=fake
        access=JudgeAccess(tmp_path/'access.sqlite3');token=principal.set(access.validate(access.issue()))
        repo=Repository(tmp_path/'state.sqlite3');s=repo.save(Snapshot(original_request='Task',current_request='Task',stage='post',intent=intent,answer=answer),'start','initial',claim=True)
        svc=Interactions(repo,BoundedProvider(provider,access));action=Action(operation_id='post',expected_revision=s.revision)
        try:
            if fatal:
                with pytest.raises(StageFailure):await svc.act(s.interaction_id,'post',action)
            else:await svc.act(s.interaction_id,'post',action)
            saved=repo.get(s.interaction_id)
            assert saved.answer==answer and saved.intent==intent and saved.model_calls[-1].total_tokens==30
            assert saved.diagnostics[-1].call_id==saved.model_calls[-1].call_id
            assert saved.diagnostics[-1].response_id=='resp-test'
            if fatal:assert saved.failed_action=='post' and saved.post is None
            else:
                assert saved.stage=='post_reviewed' and not saved.failure
                assert saved.post.assessments[0].status==Status.needs_review
                assert saved.post.assessments[1].status==Status.complete
                assert saved.post.assessments[0].evidence==[]
            await svc.act(s.interaction_id,'post',action);assert count==1
            with access.connect() as db:assert db.execute('select sum(tokens) from reservations').fetchone()[0]==30
            assert repo.trace(s.interaction_id)[-1]['snapshot'].diagnostics
        finally:principal.reset(token);await provider.client.close()
    asyncio.run(run())


def test_persistence_failure_keeps_pending_state_and_logs_safe_diagnostic(tmp_path,caplog):
    repo=Repository(tmp_path/'persist.sqlite3');s=repo.save(Snapshot(original_request='Task',current_request='Task',pending_operation='op',pending_action='post'),'start','op',claim=True)
    def broken(*args): raise sqlite3.OperationalError('PRIVATE DATABASE PATH')
    repo._finish=broken
    with pytest.raises(sqlite3.OperationalError):repo.finish(s,'op','post_completed')
    assert repo.get(s.interaction_id).pending_operation=='op'
    assert 'snapshot_event_transaction_failed' in caplog.text and 'PRIVATE DATABASE PATH' not in caplog.text

@pytest.mark.parametrize('kind', ['refusal', 'malformed', 'commentary', 'multiple', 'private_field'])
def test_public_decode_envelope_and_safe_diagnostics(tmp_path, kind):
    async def run():
        provider = OpenAIProvider(load_settings(tmp_path, {'OPENAI_API_KEY':'test-only'}))
        valid = json.dumps(dict(readiness='green', findings=[], clarifications=[], requirements=['Compare costs'], improved_prompt='Compare costs'))
        r = response(valid)
        if kind == 'refusal':
            from openai.types.responses import Response
            data = r.model_dump()
            data['output'][0]['content'] = [dict(type='refusal', refusal='PRIVATE REFUSAL')]
            r = Response.model_validate(data)
        elif kind == 'malformed': r.output[0].content[0].text = '{'
        elif kind == 'private_field': r.output[0].content[0].text = valid[:-1]+',"PRIVATE-FIELD":"PRIVATE-VALUE"}'
        elif kind == 'multiple': r.output.append(r.output[0].model_copy(deep=True))
        elif kind == 'commentary':
            commentary = r.output[0].model_copy(deep=True)
            commentary.phase = 'commentary'
            commentary.content[0].text = 'Not the structured final answer.'
            r.output.insert(0, commentary)
        sent = []
        async def fake(**kwargs): sent.append(kwargs); return r
        provider.client.responses.create = fake
        bucket=[]; token=calls.set(bucket)
        try:
            if kind == 'commentary':
                assert (await provider.generate_structured({'request':'Compare costs'}, PREProposal, 'pre')).requirements
            else:
                with pytest.raises(ReviewFailure): await provider.generate_structured({'request':'Compare costs'}, PREProposal, 'pre')
                assert bucket[0].diagnostics
            assert len(sent)==1 and bucket[0].total_tokens==30
            assert 'PRIVATE' not in bucket[0].model_dump_json()
        finally: calls.reset(token); await provider.client.close()
    asyncio.run(run())


def test_real_wire_adapter_full_cycle_without_inference(tmp_path):
    async def run():
        provider=OpenAIProvider(load_settings(tmp_path, {'OPENAI_API_KEY':'test-only'}))
        raw=judgments(); raw['r1']=dict(status='missing',explanation='No timing supplied.',evidence=[],uncertainty_reason=None,consistency_findings=[])
        verified=judgments(); verified['r1']['evidence'][0]['answer_index']=1
        outputs=[json.dumps(dict(readiness='green',findings=[],clarifications=[],requirements=['Compare cost.','Compare timing.'],improved_prompt='Compare cost and timing.')),
                 'Cost is 20.',json.dumps(raw),'{"text":"Provide the delivery timing only."}','Delivery takes two weeks.',json.dumps(verified)]
        sent=[]
        async def fake(**kwargs): sent.append(kwargs); return response(outputs[len(sent)-1])
        provider.client.responses.create=fake
        repo=Repository(tmp_path/'cycle.sqlite3'); svc=Interactions(repo,provider)
        try:
            s=await svc.start(Action(operation_id='pre',request_text='Compare cost and timing.'))
            for action, extra in [('approve-intent',dict(choice='original')),('answer',{}),('post',{}),('next',{}),('followup',{}),('verify',{})]:
                s=await svc.act(s.interaction_id,action,Action(operation_id=action,expected_revision=s.revision,**extra))
            assert s.lifecycle_status=='Complete after verification'
            assert len(sent)==6 and len(s.model_calls)==6
            assert sum(c.total_tokens for c in s.model_calls)==180
            assert s.next.target_requirement_ids==[s.intent.requirements[1].requirement_id]
            assert s.verification.assessments[1].evidence[0].response_id==s.followup_answer.response_id
            assert Repository(repo.path).get(s.interaction_id).verification==s.verification
        finally: await provider.client.close()
    asyncio.run(run())
