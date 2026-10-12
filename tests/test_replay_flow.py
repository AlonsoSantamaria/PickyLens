from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import create_app
from app.core.contracts import Assessment, Evaluation, Evidence, NextProposal, Status
from app.services.replay import load_fixture, acquire
from app.storage.repository import Repository
from devtools.stub_provider import StubProvider
def act(client, state, action, **data):
    response=client.post(f"/api/interactions/{state['interaction_id']}/{action}",json={"operation_id":str(uuid4()),"expected_revision":state["revision"],**data})
    assert response.status_code==200, response.text
    return response.json()



class PipelineProbe(StubProvider):
    """Scripted route verification, not a semantic evaluator or runtime replay result."""
    async def generate_structured(self, context, schema, purpose):
        if purpose == "pre":
            return await super().generate_structured(context, schema, purpose)
        self.calls.append(purpose)
        if purpose == "next":
            return NextProposal(text="Correct only the inconsistent claims and identify which statements they replace.", target_requirement_ids=context["allowed_targets"])
        rows=[]
        for index, req in enumerate(context["intent"]["requirements"]):
            answer=context["answers"][-1]
            rows.append(Assessment(requirement_id=req["requirement_id"], requirement_text=req["text"],
                status=Status.partial if context["phase"]=="post" and index==1 else Status.complete,
                explanation="Scripted test assessment", evidence=[Evidence(response_id=answer["response_id"], excerpt=answer["text"][:30], location="Test excerpt")]))
        return Evaluation(intent_version=context["intent"]["version"], phase=context["phase"], assessments=rows)


def canonical(client):
    response=client.post("/api/interactions/pre",json={"operation_id":str(uuid4()),"mode":"replay","canonical_scenario":True})
    assert response.status_code==200, response.text
    return act(client,response.json(),"approve-canonical")


def test_only_first_response_is_replaced_and_full_trace_survives(tmp_path):
    provider=PipelineProbe(); db=tmp_path/"replay.sqlite3"
    client=TestClient(create_app(provider,db)); s=canonical(client)
    s=act(client,s,"answer")
    assert s["answer"]["text"]==load_fixture()["response"]["text"]
    assert provider.calls==["pre"]
    s=act(client,s,"post"); s=act(client,s,"next")
    targets=[a["requirement_id"] for a in s["post"]["assessments"] if a["status"]=="partial"]
    assert s["next"]["target_requirement_ids"]==targets
    assert "Correct only" in s["followup_draft"]
    s=act(client,s,"followup"); s=act(client,s,"verify")
    assert s["lifecycle_status"]=="Complete after verification"
    assert provider.calls==["pre","evaluate","next","followup","evaluate"]
    assert Repository(db).get(s["interaction_id"]).verification


def test_mode_change_preserves_intent_and_requires_confirmation(tmp_path):
    provider=PipelineProbe();db=tmp_path/"modes.sqlite3";client=TestClient(create_app(provider,db))
    s=canonical(client);intent=s["intent"];pre=s["pre"]
    s=act(client,s,"mode",mode="live")
    assert s["intent"]==intent and s["pre"]==pre and provider.calls==["pre"]
    s=act(client,s,"answer");s=act(client,s,"post")
    old=s["answer"]["text"]
    rejected=client.post(f"/api/interactions/{s['interaction_id']}/mode",json={"operation_id":str(uuid4()),"expected_revision":s["revision"],"mode":"replay"})
    assert rejected.status_code==422
    s=act(client,s,"mode",mode="replay",confirmed_switch=True)
    assert s["answer"] is None and s["post"] is None and s["stage"]=="ai"
    assert s["intent"]==intent and s["pre"]==pre
    assert any(event["snapshot"].answer and event["snapshot"].answer.text == old for event in Repository(db).trace(s["interaction_id"]))


def test_unbound_intent_blocks_replay_and_offers_live(tmp_path):
    client=TestClient(create_app(PipelineProbe(),tmp_path/"invalid.sqlite3"))
    s=client.post("/api/interactions/pre",json={"operation_id":str(uuid4()),"request_text":"Compare new alternatives","mode":"replay"}).json()
    s=act(client,s,"approve-intent",choice="original")
    result=client.post(f"/api/interactions/{s['interaction_id']}/answer",json={"operation_id":str(uuid4()),"expected_revision":s["revision"]})
    assert result.status_code==422 and "Live Model" in result.text


def test_wording_is_not_the_compatibility_key(tmp_path):
    from app.core.contracts import ApprovedIntent
    client=TestClient(create_app(PipelineProbe(),tmp_path/"words.sqlite3"))
    intent=ApprovedIntent.model_validate(canonical(client)["intent"])
    intent.approved_prompt="Equivalent display wording under the same explicit canonical binding."
    intent.requirements[0].text="Compare both options concisely."
    assert acquire(intent).text==load_fixture()["response"]["text"]
    intent.replay_binding["constraints"]["option_b_weeks"]=99
    import pytest
    with pytest.raises(ValueError): acquire(intent)
