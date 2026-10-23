"""Bounded final acceptance runner. No repair, capture retries, or implicit calls."""
import json
import threading
import time
from pathlib import Path
from uuid import uuid4
from fastapi.testclient import TestClient
from app.config import load_settings
from app.main import create_app
from app.providers.openai_adapter import OpenAIProvider
from app.services.judge_access import JudgeAccess
from app.core.contracts import now

DEST=Path('work/final-validation-2026-10-23')
DEST.mkdir(parents=True,exist_ok=True)

class Recorder:
    def __init__(self):
        self.lock=threading.Lock()
        path=DEST/'calls.json'
        self.records=json.loads(path.read_text()) if path.exists() else []
    def save(self):
        (DEST/'calls.json').write_text(json.dumps(self.records,indent=2),encoding='utf-8')
    def begin(self,purpose,args):
        with self.lock:
            if len(self.records)>=6:raise ValueError('Authorized six-call maximum reached')
            record={'number':len(self.records)+1,'purpose':purpose,'started_at':now(),
                    'requested_model':args['model'],'reasoning':args['reasoning'],
                    'status':'attempted','start_clock':time.time()}
            self.records.append(record);self.save()
            return record
    def fail(self,record,error_type,status,code):
        record.update(status='failed',error_type=error_type,http_status=status,error_code=code,
                      duration_ms=round((time.time()-record['start_clock'])*1000,2));self.save()
    def finish(self,record,response):
        record.update(status=response.status,returned_model=response.model,response_id=response.id,
                      usage=response.usage.model_dump() if response.usage else None,
                      duration_ms=round((time.time()-record['start_clock'])*1000,2),completed_at=now())
        self.save()
        (DEST/f"response-{record['number']}.json").write_text(response.model_dump_json(indent=2),encoding='utf-8')

settings=load_settings()
if not settings.api_key.get_secret_value():raise RuntimeError('Live configuration unavailable')
if settings.model!='gpt-5.6-sol' or settings.reasoning_effort!='low':raise RuntimeError('Model/effort differ from approved validation')
access=JudgeAccess(DEST/'access.sqlite3',global_limit=6,per_minute=6,token_limit=2000000)
pass_file=DEST/'judge-pass.txt'
if not pass_file.exists():pass_file.write_text(access.issue(maximum=6,hours=72),encoding='utf-8')
recorder=Recorder()
app=create_app(OpenAIProvider(settings,recorder),DEST/'web.sqlite3',internal_tools=False,access=access)

PROMPT='Compare a paper checklist and a shared spreadsheet for a two-person bakery. Give exactly three practical tradeoffs, recommend one option with a reason, and state one assumption. Keep the answer under 180 words.'

def web():
    if recorder.records:raise RuntimeError('Evidence already exists; do not repeat Web validation')
    with TestClient(app) as client:
        headers={'Authorization':'Bearer '+pass_file.read_text().strip()}
        def action(name,s=None,**values):
            payload={'operation_id':str(uuid4()),**values}
            url='/api/interactions/pre'
            if s:
                payload['expected_revision']=s['revision'];url=f"/api/interactions/{s['interaction_id']}/{name}"
            r=client.post(url,json=payload,headers=headers)
            if r.status_code!=200:raise RuntimeError(f'{name} failed HTTP {r.status_code}; no retry')
            snapshot=r.json();(DEST/'web-snapshot.json').write_text(json.dumps(snapshot,indent=2),encoding='utf-8')
            return snapshot
        s=action('pre',request_text=PROMPT,mode='live')
        print('PRE readiness:',s['pre']['readiness'],flush=True)
        if s['pre']['readiness']=='red':raise RuntimeError('Red PRE requires review; stopped before answer')
        s=action('approve-intent',s,choice='original')
        s=action('answer',s)
        s=action('post',s)
        print('POST:',{key:sum(a['status']==key for a in s['post']['assessments']) for key in ['complete','partial','missing','needs_review']},flush=True)
        assert client.get('/interactions',headers=headers).status_code==200
        assert 'Replay' not in client.get('/',headers=headers).text
        print('Web API journey, History and live-only page checks passed.',flush=True)
    print(json.dumps(recorder.records,indent=2),flush=True)

if __name__=='__main__':web()
