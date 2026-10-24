import asyncio
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.services.judge_access import JudgeAccess, AccessDenied, BoundedProvider, principal
from devtools.stub_provider import StubProvider


def test_invalid_expired_and_global_limits(tmp_path):
    access=JudgeAccess(tmp_path/'access.db',global_limit=2)
    with pytest.raises(AccessDenied):access.validate('invalid')
    token=access.issue(2); key=access.validate(token)
    ctx=principal.set(key)
    try:
        access.reserve();access.reserve()
        with pytest.raises(AccessDenied,match='allowance'):access.reserve()
    finally:principal.reset(ctx)
    with access.connect() as db:db.execute('UPDATE passes SET expires=0')
    with pytest.raises(AccessDenied,match='expired'):access.validate(token)


def test_atomic_concurrent_reservations(tmp_path):
    access=JudgeAccess(tmp_path/'access.db',global_limit=3,per_minute=20)
    key=access.validate(access.issue(3))
    def attempt(_):
        ctx=principal.set(key)
        try:
            access.reserve();return True
        except AccessDenied:return False
        finally:principal.reset(ctx)
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(attempt,range(12)))==3


def test_rate_limit_and_restart(tmp_path):
    access=JudgeAccess(tmp_path/'access.db',global_limit=5,per_minute=1)
    token=access.issue(5);ctx=principal.set(access.validate(token))
    try:
        access.reserve()
        with pytest.raises(AccessDenied,match='wait'):access.reserve()
        restarted=JudgeAccess(tmp_path/'access.db',global_limit=1)
        with pytest.raises(AccessDenied,match='allowance'):restarted.reserve()
    finally:principal.reset(ctx)


def test_browser_pass_blocks_provider_and_explicit_post(tmp_path):
    access=JudgeAccess(tmp_path/'access.db',global_limit=4)
    provider=StubProvider()
    client=TestClient(create_app(provider,tmp_path/'web.db',access=access))
    assert client.post('/api/browser/pre',json={'request':'Task'}).status_code==401
    assert provider.calls==[]
    headers={'Authorization':'Bearer '+access.issue(4)}
    pre=client.post('/api/browser/pre',json={'request':'Task'},headers=headers)
    assert pre.status_code==200
    post=client.post('/api/browser/post',json={'request':'Task','answer':'A response'},headers=headers)
    assert post.status_code==200,post.text
    assert len(provider.calls)==3
    client.post('/api/browser/pre',json={'request':'Task'},headers=headers)
    denied=client.post('/api/browser/pre',json={'request':'Task'},headers=headers)
    assert denied.status_code==429 and 'allowance' in denied.json()['detail']
    assert len(provider.calls)==4


def test_web_anonymous_cookie_origin_and_history_isolation(tmp_path):
    access=JudgeAccess(tmp_path/'access.db')
    provider=StubProvider()
    app=create_app(provider,tmp_path/'web.db',access=access)
    client=TestClient(app,base_url='https://testserver')
    other=TestClient(app,base_url='https://testserver')
    page=client.get('/')
    assert page.status_code==200 and 'Judge Pass' not in page.text
    assert 'HttpOnly' in page.headers['set-cookie'] and 'Secure' in page.headers['set-cookie']
    assert client.get('/interactions').status_code==200
    payload={'operation_id':'same','request_text':'Task'}
    assert client.post('/api/interactions/pre',json=payload,headers={'Origin':'https://evil.invalid'}).status_code==403
    result=client.post('/api/interactions/pre',json=payload,headers={'Origin':'https://testserver'})
    assert result.status_code==200,result.text
    id=result.json()['interaction_id']
    assert client.get('/api/interactions/'+id).status_code==200
    assert other.get('/api/interactions/'+id).status_code==404
    assert other.get('/interactions/'+id).status_code==404
    assert other.get('/?interaction='+id).status_code==404
    assert id not in other.get('/interactions').text
    second=other.post('/api/interactions/pre',json=payload,headers={'Origin':'https://testserver'})
    assert second.status_code==200 and second.json()['interaction_id']!=id
    # Anonymous cookies and legacy pass cookies cannot authorize the extension API.
    assert client.post('/api/browser/pre',json={'request':'Task'}).status_code==401
    assert client.post('/api/browser/pre',json={'request':'Task'},headers={'Authorization':'Bearer '+client.cookies['pickylens_demo']}).status_code==401
    assert client.get('/access',follow_redirects=False).headers['location']=='/'


def test_long_context_and_failures_are_bounded(tmp_path):
    access=JudgeAccess(tmp_path/'access.db',global_limit=1)
    provider=StubProvider();bounded=BoundedProvider(provider,access)
    ctx=principal.set(access.validate(access.issue(1)))
    try:
        with pytest.raises(AccessDenied,match='too long'):
            asyncio.run(bounded.generate_text({'prompt':'x'*60001},'answer'))
        assert provider.calls==[]
    finally:principal.reset(ctx)

def test_packaging_narrow_origin_no_loopback(tmp_path):
    import json
    from zipfile import ZipFile
    from devtools.package_browser import package
    output=tmp_path/'extension.zip'
    package('https://demo.example.test',output)
    with ZipFile(output) as bundle:
        manifest=json.loads(bundle.read('manifest.json'))
        assert manifest['host_permissions']==['https://demo.example.test/*']
        assert b'127.0.0.1' not in bundle.read('worker.js')
        assert manifest['permissions']==['storage']
    with pytest.raises(ValueError):package('https://user:secret@example.test',tmp_path/'bad.zip')
    with pytest.raises(ValueError):package('http://example.test',tmp_path/'bad.zip')


def test_failed_call_consumes_allowance(tmp_path):
    class FailingProvider:
        test_stub=True
        calls=0
        async def generate_text(self,*args):
            self.calls+=1
            raise RuntimeError('failed')
    access=JudgeAccess(tmp_path/'access.db',global_limit=1)
    raw=FailingProvider();provider=BoundedProvider(raw,access)
    ctx=principal.set(access.validate(access.issue(1)))
    try:
        with pytest.raises(RuntimeError):asyncio.run(provider.generate_text({'prompt':'Task'},'answer'))
        with pytest.raises(AccessDenied):asyncio.run(provider.generate_text({'prompt':'Task'},'answer'))
        assert raw.calls==1
    finally:principal.reset(ctx)

def test_token_ceiling_reservation_and_settlement(tmp_path):
    from app.core.contracts import ModelCall
    access=JudgeAccess(tmp_path/'tokens.db',global_limit=30,token_limit=300100)
    ctx=principal.set(access.validate(access.issue(30)))
    try:
        reservation=access.reserve()
        with pytest.raises(AccessDenied):access.reserve()
        access.settle(reservation,[ModelCall(provider='test',model='test',purpose='pre',total_tokens=100)])
        pending=access.reserve()
        with pytest.raises(AccessDenied):access.reserve()
        access.settle(pending,[])
        with pytest.raises(AccessDenied):access.reserve()
        restarted=JudgeAccess(tmp_path/'tokens.db',global_limit=30,token_limit=300100)
        with pytest.raises(AccessDenied):restarted.reserve()
    finally:principal.reset(ctx)


def test_anonymous_limits_survive_cookie_rotation_and_restart(tmp_path):
    access=JudgeAccess(tmp_path/'access.db',anonymous_operations=1,anonymous_per_minute=10,anonymous_ip_operations=2)
    identity,cookie=access.anonymous('', '127.0.0.2')
    assert access.anonymous(cookie,'127.0.0.2')==(identity,None)
    def reserve(key):
        token=principal.set(key)
        try:return access.reserve()
        finally:principal.reset(token)
    reserve(identity)
    with pytest.raises(AccessDenied,match='Public demo allowance'):reserve(identity)
    other,_=access.anonymous('', '127.0.0.2');reserve(other)
    fresh,_=access.anonymous('', '127.0.0.2')
    with pytest.raises(AccessDenied,match='Public demo allowance'):reserve(fresh)
    access=JudgeAccess(tmp_path/'access.db',anonymous_ip_operations=2)
    with pytest.raises(AccessDenied,match='Public demo allowance'):reserve(fresh)
    with access.connect() as db:
        assert db.execute('SELECT count(*) FROM reservations').fetchone()[0]==2
        assert db.execute("SELECT count(*) FROM passes WHERE ip_digest='127.0.0.2'").fetchone()[0]==0


@pytest.mark.parametrize('limit,tokens',[(1,2000000),(200,300000)])
def test_global_breakers_shared_between_anonymous_and_extension(tmp_path,limit,tokens):
    access=JudgeAccess(tmp_path/'access.db',global_limit=limit,token_limit=tokens)
    judge=access.validate(access.issue(1))
    anonymous,_=access.anonymous('', '127.0.0.3')
    ctx=principal.set(anonymous)
    try:access.reserve()
    finally:principal.reset(ctx)
    ctx=principal.set(judge)
    try:
        with pytest.raises(AccessDenied):access.reserve()
    finally:principal.reset(ctx)


def test_anonymous_ip_rate_limit_is_atomic(tmp_path):
    access=JudgeAccess(tmp_path/'access.db',anonymous_per_minute=2)
    identities=[access.anonymous('', '127.0.0.4')[0] for _ in range(8)]
    def attempt(key):
        ctx=principal.set(key)
        try:access.reserve();return True
        except AccessDenied:return False
        finally:principal.reset(ctx)
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(attempt,identities))==2


def test_web_allowance_failure_preserves_work_without_provider_call(tmp_path):
    access=JudgeAccess(tmp_path/'access.db',anonymous_operations=1)
    provider=StubProvider();client=TestClient(create_app(provider,tmp_path/'web.db',access=access))
    headers={'Origin':'http://testserver'}
    first=client.post('/api/interactions/pre',json={'operation_id':'one','request_text':'Task'},headers=headers)
    assert first.status_code==200
    failed=client.post('/api/interactions/pre',json={'operation_id':'two','request_text':'Task'},headers=headers)
    assert failed.status_code==429 and 'Public demo allowance reached' in failed.text
    assert len(provider.calls)==1
    assert client.get('/api/interactions/'+first.json()['interaction_id']).status_code==200
