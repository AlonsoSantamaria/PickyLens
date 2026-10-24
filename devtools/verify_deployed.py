"""Verify deployed access from outside VESTA, without provider calls or secret output."""
import json
import subprocess
from pathlib import Path
import httpx

def remote(command):
    result=subprocess.run(['ssh','-o','BatchMode=yes','vesta',command],capture_output=True,text=True)
    if result.returncode:raise RuntimeError('Remote verification helper failed; output withheld')
    return result.stdout.strip()
root='/srv/neovantia/apps/pickylens'
script="from app.services.judge_access import JudgeAccess; a=JudgeAccess('/var/lib/neovantia/pickylens/judge-access.sqlite3'); t=a.issue(1,1); db=a.connect(); db.execute('UPDATE passes SET used=maximum WHERE digest=?',(a.digest(t),)); db.commit(); print(t)"
exhausted=remote('cd '+root+' && .venv/bin/python -c "'+script+'"')

count="import sqlite3; db=sqlite3.connect('/var/lib/neovantia/pickylens/judge-access.sqlite3'); print(db.execute('SELECT count(*) FROM reservations').fetchone()[0])"
count_command='cd '+root+' && .venv/bin/python -c "'+count+'"'
before=int(remote(count_command))
with httpx.Client(base_url='https://pickylens.neovantia.live',timeout=20) as client:
    assert client.get('/access').status_code==303
    invalid=client.post('/api/browser/pre',headers={'Authorization':'Bearer invalid'},json={'request':'denial check'})
    denied=client.post('/api/browser/pre',headers={'Authorization':'Bearer '+exhausted},json={'request':'denial check'})
    assert invalid.status_code==401 and denied.status_code==429,(invalid.status_code,denied.status_code)
    page=client.get('/')
    assert page.status_code==200
    assert 'Secure' in page.headers['set-cookie'] and 'HttpOnly' in page.headers['set-cookie']
    assert 'Judge Pass' not in page.text
    assert all(term not in page.text for term in ['Replay','Deterministic test environment','synthetic','Live AI is not configured'])
    assert client.get('/interactions').status_code==200
    Path('work/deployed-workspace.html').write_text(page.text,encoding='utf-8')
after=int(remote(count_command))
assert before==after
report={'https':200,'workspace':200,'history':200,'invalid':401,'exhausted':429,'secure_cookie':True,'provider_calls_added':after-before,'public_replay_or_test_ui':False}
Path('work/deployment-checks.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
