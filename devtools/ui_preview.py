"""Local deterministic UI fixture server. Never invokes providers; no production deployment."""
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.core.contracts import Snapshot, Answer, ApprovedIntent, Requirement, PREProposal, Finding, Assessment, Evaluation, Evidence, NextProposal

app=FastAPI()
app.mount('/static',StaticFiles(directory='app/static'),name='static')
templates=Jinja2Templates(directory='app/templates')
source=Path('tests/fixtures/answer-markdown.md').read_text(encoding='utf-8')

@app.get('/{kind}')
async def preview(request: Request, kind: str):
    long=kind!='short'
    prompt=('Review the operational options. Explain cost, timing and risk.\n'*70) if long else 'Compare two options.'
    answer=(source+'\n\n'+('A long paragraph with wrapping text and useful information. '*25+'\n\n')*25) if long else '**Short answer.** One clear recommendation.'
    requirements=[Requirement(requirement_id=f'r{i}',text=f'Requirement {i+1}: compare operational alternatives.') for i in range(24 if long else 1)]
    initial=Answer(response_id='first',text=answer)
    followup=Answer(response_id='followup',text=answer)
    assessments=[Assessment(requirement_id=r.requirement_id,requirement_text=r.text,status=['complete','partial','missing','needs_review'][i%4],explanation='Synthetic evaluation for UI testing.',evidence=[Evidence(response_id='first',excerpt='Long exact-looking synthetic evidence. '*120,location='Example section')]) for i,r in enumerate(requirements)]
    s=Snapshot(interaction_id='ui-fixture',original_request=prompt,current_request=prompt,selected_prompt=prompt,stage='verified',test_stub=True,
        intent=ApprovedIntent(version=1,original_request=prompt,approved_prompt=prompt,approval_action='original',accepted_clarifications={},requirements=requirements),
        answer=initial,post=Evaluation(intent_version=1,phase='post',assessments=assessments),
        next=NextProposal(text=prompt,target_requirement_ids=['r0']),followup_draft=prompt,followup_answer=followup,
        verification=Evaluation(intent_version=1,phase='verify',assessments=assessments))
    if kind=='pre':
        s.stage='pre';s.intent=s.answer=s.post=s.next=s.followup_answer=s.verification=None
        s.pre=PREProposal(readiness='amber',findings=[Finding(title='Consider priority',explanation='A material issue. '*80)],clarifications=[],requirements=requirements,improved_prompt=prompt)
    return templates.TemplateResponse(request=request,name='workspace.html',context={'snapshot':s,'prompt':prompt,'description':'Deterministic presentation fixture. No provider calls.','stub':True,'internal_tools':False,'live_configured':True,'demo':None})
