import asyncio
import sqlite3
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.core.contracts import Snapshot, Action, Evaluation, NextProposal, Status
from app.core.evaluation import evaluate
from app.core.next import generate
from app.storage.repository import Repository
from app.services.scenario import PROMPT
from devtools.stub_provider import StubProvider


@pytest.fixture
def setup(tmp_path):
    provider = StubProvider()
    db = tmp_path / "test.sqlite3"
    app = create_app(provider, db)
    return TestClient(app), provider, db


def start(client, text=PROMPT):
    response = client.post("/api/interactions/pre", json={"operation_id": str(uuid4()), "request_text": text})
    assert response.status_code == 200, response.text
    return response.json()


def act(client, s, action, **data):
    response = client.post(f"/api/interactions/{s['interaction_id']}/{action}", json={
        "operation_id": str(uuid4()), "expected_revision": s["revision"], **data})
    assert response.status_code == 200, response.text
    return response.json()


def approved(client, choice="improved"):
    s = start(client)
    if choice == "improved":
        s = act(client, s, "clarifications", clarifications={"priority": "Lowest upfront cost"})
    return act(client, s, "approve-intent", choice=choice)


def test_full_golden_path_and_restart(setup):
    client, provider, db = setup
    s = approved(client)
    frozen = s["intent"]
    assert len(frozen["requirements"]) == 9
    s = act(client, s, "answer")
    s = act(client, s, "post")
    statuses = [a["status"] for a in s["post"]["assessments"]]
    assert statuses.count("complete") == 8 and statuses.count("missing") == 1
    missing = [a["requirement_id"] for a in s["post"]["assessments"] if a["status"] == "missing"]
    s = act(client, s, "next")
    assert s["next"]["target_requirement_ids"] == missing
    assert s["followup_answer"] is None
    assert provider.calls == ["pre", "answer", "evaluate", "next"]
    edited = s["followup_draft"] + " Keep this concise."
    s = act(client, s, "followup-draft", prompt=edited)
    reopened = TestClient(create_app(StubProvider(), db))
    saved = reopened.get(f"/api/interactions/{s['interaction_id']}").json()
    assert saved["followup_draft"] == edited and saved["intent"] == frozen
    assert "Resume interaction" in reopened.get(f"/interactions/{s['interaction_id']}").text
    s = act(client, s, "followup")
    assert s["verification"] is None and s["stage"] == "verify"
    s = act(client, s, "verify")
    assert s["lifecycle_status"] == "Complete after verification"
    assert all(a["status"] == "complete" for a in s["verification"]["assessments"])
    assert [a["requirement_id"] for a in s["post"]["assessments"]] == [a["requirement_id"] for a in s["verification"]["assessments"]]
    resolved = next(a for a in s["verification"]["assessments"] if a["requirement_id"] == missing[0])
    assert resolved["evidence"][0]["response_id"] == s["followup_answer"]["response_id"]
    detail = reopened.get(f"/interactions/{s['interaction_id']}")
    assert detail.status_code == 200 and "Resume interaction" not in detail.text
    assert edited in detail.text and "Post Completed" in detail.text
    assert reopened.get(f"/?interaction={s['interaction_id']}", follow_redirects=False).status_code == 307
    assert len(Repository(db).list()) == 1
    with sqlite3.connect(db) as connection:
        sequence = [row[0] for row in connection.execute("SELECT sequence_number FROM interaction_events ORDER BY sequence_number")]
        assert sequence == list(range(1, len(sequence) + 1))
    assert provider.calls == ["pre", "answer", "evaluate", "next", "followup", "evaluate"]


def test_workspace_and_blank_requests_create_no_history(setup):
    client, provider, db = setup
    assert client.get("/").status_code == 200
    assert "No interactions yet." in client.get("/interactions").text
    response = client.post("/api/interactions/pre", json={"operation_id": str(uuid4()), "request_text": "   "})
    assert response.status_code == 422 and provider.calls == []
    assert Repository(db).list() == []
    assert "not Replay Demo" in client.get("/").text


def test_original_does_not_adopt_pre_suggestion(setup):
    client, _, _ = setup
    s = start(client)
    s = act(client, s, "clarifications", clarifications={"priority": "Lowest upfront cost"})
    s = act(client, s, "approve-intent", choice="original")
    assert s["intent"]["accepted_clarifications"] == {}
    assert len(s["intent"]["requirements"]) == 8
    assert s["selected_prompt"] == PROMPT.strip()


def test_improved_requires_human_decision(setup):
    client, _, _ = setup
    s = start(client)
    response = client.post(f"/api/interactions/{s['interaction_id']}/approve-intent", json={
        "operation_id": str(uuid4()), "expected_revision": s["revision"], "choice": "improved"})
    assert response.status_code == 422
    assert client.get(f"/api/interactions/{s['interaction_id']}").json()["intent"] is None


def test_verify_cannot_run_before_followup(setup):
    client, _, _ = setup
    s = approved(client)
    response = client.post(f"/api/interactions/{s['interaction_id']}/verify", json={
        "operation_id": str(uuid4()), "expected_revision": s["revision"]})
    assert response.status_code == 422


def test_atomic_rollback_on_failed_event_insert(tmp_path):
    repo = Repository(tmp_path / "atomic.sqlite3")
    s = Snapshot(original_request="request", current_request="request")
    op = str(uuid4())
    s = repo.save(s, "interaction_started", op, claim=True)
    before = repo.get(s.interaction_id)
    s.title = "Must not commit"
    with pytest.raises(sqlite3.IntegrityError):
        repo.save(s, "intent_approved", op, s.revision, claim=True)
    assert repo.get(s.interaction_id) == before
    assert len(repo.trace(s.interaction_id)) == 1


def test_typed_payload_rejection_before_persistence(tmp_path):
    repo = Repository(tmp_path / "typed.sqlite3")
    s = Snapshot(original_request="request", current_request="request")
    s.revision = "invalid"
    with pytest.raises(ValueError):
        repo.save(s, "interaction_started", str(uuid4()), claim=True)
    assert repo.list() == []


def test_first_pre_failure_preserves_request(tmp_path):
    class Broken(StubProvider):
        async def generate_structured(self, *args):
            raise ValueError("Controlled test failure")
    app = create_app(Broken(), tmp_path / "failure.sqlite3")
    client = TestClient(app)
    response = client.post("/api/interactions/pre", json={"operation_id": str(uuid4()), "request_text": PROMPT})
    assert response.status_code == 502
    saved = app.state.repository.list()[0]
    assert saved.original_request == PROMPT.strip() and saved.lifecycle_status == "Failed at PRE"
    assert saved.pre is None and "PRE" in saved.failure


@pytest.mark.parametrize("corruption", ["excerpt", "coverage", "identity"])
def test_invalid_evidence_or_coverage_rejected(setup, corruption):
    client, _, _ = setup
    s = approved(client)
    s = act(client, s, "answer")
    snapshot = Snapshot.model_validate(s)
    class Corrupt(StubProvider):
        async def generate_structured(self, context, schema, purpose):
            result = await super().generate_structured(context, schema, purpose)
            if corruption == "excerpt":
                result.assessments[0].evidence[0].excerpt = "Invented quotation that is not in the answer"
            elif corruption == "coverage":
                result.assessments.pop()
            else:
                result.assessments[0].requirement_text = "Redefined intent"
            return result
    with pytest.raises(ValueError):
        asyncio.run(evaluate(Corrupt(), snapshot.intent, [snapshot.answer], "post"))


def test_next_excludes_unapproved_uncertainty_and_complete_targets(setup):
    client, _, _ = setup
    s = approved(client)
    s = act(client, s, "answer")
    s = act(client, s, "post")
    snapshot = Snapshot.model_validate(s)
    class Overreaching(StubProvider):
        async def generate_structured(self, context, schema, purpose):
            return NextProposal(text="Rewrite everything", target_requirement_ids=[snapshot.intent.requirements[0].requirement_id])
    with pytest.raises(ValueError):
        asyncio.run(generate(Overreaching(), snapshot.intent, snapshot.post, snapshot.answer))
    for assessment in snapshot.post.assessments:
        assessment.status = Status.needs_review
    with pytest.raises(ValueError, match="No repairable"):
        asyncio.run(generate(StubProvider(), snapshot.intent, snapshot.post, snapshot.answer))


def test_model_text_is_escaped_in_history(setup):
    client, _, _ = setup
    s = start(client, "<script>alert('unsafe')</script>")
    html = client.get(f"/interactions/{s['interaction_id']}").text
    assert "<script>alert('unsafe')</script>" not in html
    assert "&lt;script&gt;" in html
