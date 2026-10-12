import asyncio
from types import SimpleNamespace
from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import create_app, UnconfiguredProvider
from app.core.contracts import ModelCall, PREProposal, Action
from app.config import load_settings
from app.providers.openai_adapter import OpenAIProvider
from app.providers.telemetry import calls
from app.services.interactions import Interactions, StageFailure
from app.storage.repository import Repository
from devtools.stub_provider import StubProvider
from devtools.interaction_report import summarize

class PublicProbe(StubProvider):
    test_stub = False


def test_public_live_only_routes_history_and_no_fallback(tmp_path):
    provider=PublicProbe(); app=create_app(provider,tmp_path/'public.sqlite3');client=TestClient(app)
    page=client.get('/').text
    assert 'Replay' not in page and '<select id="mode"' not in page
    assert 'fixture' not in page and 'Development stub' not in page
    assert client.post('/api/interactions/pre',json={'operation_id':'blocked','request_text':'Task','mode':'replay'}).status_code==422
    assert provider.calls==[]
    s=client.post('/api/interactions/pre',json={'operation_id':'start','request_text':'Task'}).json()
    assert s['mode']=='live'
    denied=client.post('/api/interactions/'+s['interaction_id']+'/mode',json={'operation_id':'switch','expected_revision':s['revision'],'mode':'replay'})
    assert denied.status_code==422
    assert client.get('/interactions/'+s['interaction_id']).status_code==200
    assert client.get('/?interaction='+s['interaction_id']).status_code==200
    internal=TestClient(create_app(StubProvider(),tmp_path/'internal.sqlite3',internal_tools=True))
    record=internal.post('/api/interactions/pre',json={'operation_id':'internal','canonical_scenario':True,'mode':'replay'}).json()
    # Existing internal records remain stored, but are not a public product experience.
    public=TestClient(create_app(provider,tmp_path/'internal.sqlite3',internal_tools=False))
    assert public.get('/api/interactions/'+record['interaction_id']).status_code==404
    assert public.get('/interactions/'+record['interaction_id']).status_code==404
    assert 'No interactions yet.' in public.get('/interactions').text
    assert internal.app.state.repository.get(record['interaction_id']).mode=='replay'


def test_missing_configuration_explains_failure_without_synthetic_result(tmp_path):
    app=create_app(UnconfiguredProvider(),tmp_path/'missing.sqlite3');client=TestClient(app)
    assert 'Live AI is not configured' in client.get('/').text
    result=client.post('/api/interactions/pre',json={'operation_id':'missing','request_text':'Task'})
    assert result.status_code==503 and 'Live AI is not configured' in result.json()['detail']
    assert app.state.repository.list()==[]


def test_adapter_records_real_response_usage_without_network(tmp_path):
    async def run():
        provider=OpenAIProvider(load_settings(tmp_path,{'OPENAI_API_KEY':'test-only'}))
        response=SimpleNamespace(status='completed',id='response-test',model='test-model',usage=SimpleNamespace(input_tokens=10,output_tokens=6,total_tokens=16,output_tokens_details=SimpleNamespace(reasoning_tokens=2)))
        async def fake(**kwargs): return response
        provider.client.responses.create=fake
        bucket=[];token=calls.set(bucket)
        try: await provider.request([], 'answer')
        finally: calls.reset(token);await provider.client.close()
        assert len(bucket)==1 and bucket[0].input_tokens==10 and bucket[0].reasoning_tokens==2
        assert bucket[0].duration_ms>=0 and bucket[0].response_id=='response-test'
    asyncio.run(run())


def test_call_metadata_survives_failure_retry_duplicate_and_restart(tmp_path):
    class Metered(PublicProbe):
        broken=True
        async def generate_structured(self,context,schema,purpose):
            calls.get().append(ModelCall(provider='test',model='synthetic',purpose=purpose,total_tokens=12,input_tokens=8,output_tokens=4,duration_ms=2,status='failed' if self.broken else 'completed'))
            if self.broken: raise ValueError('Synthetic failure')
            return await super().generate_structured(context,schema,purpose)
    async def run():
        db=tmp_path/'metrics.sqlite3';provider=Metered();svc=Interactions(Repository(db),provider)
        try: await svc.start(Action(operation_id='first',request_text='Task'))
        except StageFailure as exc: s=exc.snapshot
        assert len(s.model_calls)==1 and s.model_calls[0].operation_id=='first'
        provider.broken=False
        action=Action(operation_id='retry',expected_revision=s.revision)
        s=await svc.act(s.interaction_id,'retry',action)
        duplicate=await svc.act(s.interaction_id,'retry',action)
        assert len(duplicate.model_calls)==2
        saved=Repository(db).get(s.interaction_id)
        report=summarize(saved)
        assert report['model_call_count']==2 and report['usage']['total_tokens']==24
        assert report['pre_readiness'] and report['post_counts'] is None
        assert calls.get() is None
    asyncio.run(run())


def test_late_call_usage_is_retained_without_current_result(tmp_path):
    repo=Repository(tmp_path/'late.sqlite3')
    from app.core.contracts import Snapshot
    s=repo.save(Snapshot(original_request='Task',current_request='Task',pending_operation='old'), 'start','old',claim=True)
    late=s.model_copy(deep=True)
    s.pending_operation=None;s.lifecycle_status='Paused'
    repo.save(s,'paused','pause',s.revision,claim=True)
    late.model_calls.append(ModelCall(provider='test',model='test',purpose='answer',operation_id='old',total_tokens=5))
    saved=repo.finish(late,'old','response_received')
    assert saved.lifecycle_status=='Paused' and saved.answer is None
    assert len(saved.model_calls)==1 and repo.trace(s.interaction_id)[-1]['type']=='superseded_result'
