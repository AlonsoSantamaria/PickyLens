from fastapi.testclient import TestClient
from app.main import create_app
from app.services.replay import load_fixture
from devtools.stub_provider import StubProvider


def test_guidance_and_empty_history(tmp_path):
    client=TestClient(create_app(StubProvider(),tmp_path/"ui.sqlite3"))
    page=client.get("/")
    assert page.status_code==200
    for phrase in ["Left: what you ask.", "Right: what the AI gives you.", "Review request", "Nothing is sent without your action"]:
        assert phrase in page.text
    assert "No interactions yet." in client.get("/interactions").text
    assert client.app.state.repository.list()==[]


def test_genuine_fixture_has_provenance_without_expected_results():
    fixture=load_fixture()
    assert fixture["provenance"]["response_id"]==fixture["response"]["metadata"]["provider_response_id"]
    assert fixture["provenance"]["usage"]["total_tokens"]>0
    assert "assessments" not in fixture and "expected_result" not in fixture
    # Capture-specific evidence belongs only in this regression check, never evaluator logic.
    assert "$17,000" in fixture["response"]["text"] and "$20,600" in fixture["response"]["text"]


def test_normal_workspace_has_no_build_debug_copy(tmp_path):
    class NoCalls(StubProvider):
        test_stub=False
    page=TestClient(create_app(NoCalls(),tmp_path/"normal.sqlite3")).get("/").text
    assert "Replay Demo" not in page and '<select id="mode"' not in page
    assert "Slice 1" not in page and "deferred to Slice" not in page
