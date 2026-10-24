"""Deployment HTTP checks only. Test passes cannot reach a model call."""
import json
import httpx2 as httpx
from app.services.judge_access import JudgeAccess
access=JudgeAccess('/var/lib/neovantia/pickylens/judge-access.sqlite3')
exhausted=access.issue(1,1)
with access.connect() as db:
    db.execute('UPDATE passes SET used=maximum WHERE digest=?',(access.digest(exhausted),))
    before=db.execute('SELECT count(*) FROM reservations').fetchone()[0]
with httpx.Client(base_url='https://pickylens.neovantia.live',timeout=20) as client:
    assert client.get('/access').status_code==303
    invalid=client.post('/api/browser/pre',headers={'Authorization':'Bearer invalid'},json={'request':'denial check'})
    denied=client.post('/api/browser/pre',headers={'Authorization':'Bearer '+exhausted},json={'request':'denial check'})
    assert invalid.status_code==401 and denied.status_code==429
    login=client.get('/')
    assert login.status_code==200
    assert 'Secure' in login.headers['set-cookie'] and 'HttpOnly' in login.headers['set-cookie']
    page=client.get('/')
    assert page.status_code==200
    assert all(term not in page.text for term in ['Replay','Deterministic test environment','synthetic','Live AI is not configured'])
    assert client.get('/interactions').status_code==200
with access.connect() as db:
    after=db.execute('SELECT count(*) FROM reservations').fetchone()[0]
assert before==after
print(json.dumps({'https':200,'workspace':200,'history':200,'invalid':401,'exhausted':429,'secure_cookie':True,'provider_calls_added':after-before,'public_replay_or_test_ui':False}))

