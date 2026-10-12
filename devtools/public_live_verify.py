"""One authorized public-flow validation; six-call ceiling, no repeated attempts."""
import json
from pathlib import Path
from uuid import uuid4
from fastapi.testclient import TestClient
from app.config import load_settings
from app.main import create_app
from app.providers.openai_adapter import OpenAIProvider
from app.services.scenario import PROMPT
from app.core.contracts import now
from devtools.interaction_report import summarize

DEST=Path("work/public-live-verification")

class Recorder:
    def __init__(self):
        DEST.mkdir(parents=True,exist_ok=False)
        self.records=[]
    def save(self):
        (DEST/"calls.json").write_text(json.dumps(self.records,indent=2),encoding="utf-8")
    def begin(self,purpose,args):
        if len(self.records)>=6: raise ValueError("Authorized six-call ceiling reached")
        r={"number":len(self.records)+1,"purpose":purpose,"started_at":now(),"requested_model":args["model"],"reasoning":args["reasoning"],"request":args["input"],"status":"attempted"}
        self.records.append(r);self.save()
        print(f"Live call {r['number']}/6: {purpose}",flush=True)
        return r
    def fail(self,r,error_type,status,code):
        r.update(status="failed",error_type=error_type,http_status=status,error_code=code,completed_at=now());self.save()
    def finish(self,r,response):
        r.update(status=response.status,response_id=response.id,returned_model=response.model,usage=response.usage.model_dump() if response.usage else None,completed_at=now());self.save()
        (DEST/f"response-{r['number']}.json").write_text(response.model_dump_json(indent=2),encoding="utf-8")

def main():
    settings=load_settings()
    if not settings.api_key.get_secret_value(): raise ValueError("Live configuration unavailable")
    if settings.model!='gpt-5.6-sol' or settings.reasoning_effort!='low': raise ValueError("Configured model/effort differs; stop for decision")
    recorder=Recorder();provider=OpenAIProvider(settings,recorder)
    app=create_app(provider,DEST/"interaction.sqlite3",internal_tools=False)
    with TestClient(app) as client:
        def act(name,s=None,**extra):
            body={"operation_id":str(uuid4()),**extra}
            url='/api/interactions/pre'
            if s:
                body['expected_revision']=s['revision'];url=f"/api/interactions/{s['interaction_id']}/{name}"
            r=client.post(url,json=body)
            if r.status_code!=200: raise ValueError(f"Stage {name} failed with HTTP {r.status_code}; inspect saved evidence before any retry")
            result=r.json()
            (DEST/"snapshot.json").write_text(json.dumps(result,indent=2),encoding='utf-8')
            return result
        s=act('pre',request_text=PROMPT,mode='live')
        if s['pre']['readiness']=='red':
            print('PRE is Red; stop for human review rather than overriding.',flush=True)
        else:
            s=act('approve-intent',s,choice='original')
            s=act('answer',s);s=act('post',s)
            repair=any(a['status'] in ('partial','missing') for a in s['post']['assessments'])
            if repair:
                s=act('next',s);s=act('followup',s);s=act('verify',s)
        snapshot=app.state.repository.get(s['interaction_id'])
        report=summarize(snapshot)
        (DEST/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps({k:v for k,v in report.items() if k!='calls'},indent=2),flush=True)
        print('Validation stopped. No additional attempts authorized by this runner.',flush=True)

if __name__=='__main__': main()
