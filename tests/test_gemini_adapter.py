import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
import pytest
from app.adapters.gemini.runner import handle
from app.adapters.gemini.protocol import HookInput
from app.adapters.gemini.presentation import render
from app.core.contracts import ModelCall, PREProposal, Requirement, Assessment, Evaluation, Evidence, NextProposal
from app.providers.telemetry import calls
from app.services.host_review import HostReview
from app.storage.repository import Repository


class Probe:
    test_stub = True

    def __init__(self, status="complete", fail=None, delay=0):
        self.status, self.fail, self.delay = status, fail, delay
        self.called = []

    async def generate_structured(self, context, schema, purpose):
        self.called.append(purpose)
        calls.get().append(ModelCall(provider="deterministic", model="probe", purpose=purpose))
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.fail == purpose:
            raise ValueError("sensitive internal error must not escape")
        if purpose == "pre":
            return PREProposal(readiness="amber", findings=[], clarifications=[],
                requirements=[Requirement(text="Compare cost")], improved_prompt="UNAPPROVED REWRITE")
        if purpose == "next":
            return NextProposal(text="Please correct the cost comparison only.",
                                target_requirement_ids=context["allowed_targets"])
        requirement = context["intent"]["requirements"][0]
        answer = context["answers"][0]
        return Evaluation(intent_version=1, phase="post", assessments=[Assessment(
            requirement_id=requirement["requirement_id"], requirement_text=requirement["text"],
            status=self.status, explanation="Cost comparison assessed.",
            evidence=[Evidence(response_id=answer["response_id"], excerpt=answer["text"], location="answer")],
            uncertainty_reason="Cost basis unclear" if self.status == "needs_review" else None)])


def hook(event="BeforeAgent", second=0, session="session", prompt="Compare cost"):
    return dict(session_id=session, cwd="C:/demo", transcript_path="C:/demo/trace.json",
                hook_event_name=event, timestamp=f"2026-10-13T12:00:{second:02d}Z", prompt=prompt,
                **({"prompt_response": "A costs 5; B costs 8.", "stop_hook_active": False}
                   if event == "AfterAgent" else {}))


def setup(tmp_path, **kwargs):
    probe = Probe(**kwargs)
    return HostReview(Repository(tmp_path / "host.sqlite3"), probe), probe


def run(value):
    return asyncio.run(value)


@pytest.mark.parametrize("status", ["complete", "partial", "missing", "needs_review"])
def test_full_hook_cycle_keeps_intent_and_never_retries(tmp_path, status):
    service, probe = setup(tmp_path, status=status)
    before = run(handle(hook(), service))
    after = run(handle(hook("AfterAgent", 1), service))
    assert set(before) == set(after) == {"decision", "systemMessage"}
    assert before["decision"] == after["decision"] == "allow"
    assert "unchanged request" in before["systemMessage"]
    s = service.repo.list()[0]
    assert s.intent.approved_prompt == "Compare cost"
    assert s.intent.accepted_clarifications == {}
    assert "extraction_not_user_confirmed" in s.intent.approval_action
    assert s.answer.text == "A costs 5; B costs 8."
    assert s.next is None and probe.called == ["pre", "evaluate"]
    assert len(s.model_calls) == 2
    assert all(c.operation_id for c in s.model_calls)
    if status == "complete":
        assert "No follow-up needed" in after["systemMessage"] and s.terminal
    elif status == "needs_review":
        assert "Uncertainty remains" in after["systemMessage"]
        assert "targeted repair" not in after["systemMessage"]
    else:
        assert "targeted repair draft" in after["systemMessage"]


def test_duplicate_delivery_is_saved_and_not_called_again(tmp_path):
    service, probe = setup(tmp_path)
    for payload in [hook(), hook("AfterAgent", 1)]:
        first = run(handle(payload, service))
        assert run(handle(payload, service)) == first
    assert probe.called == ["pre", "evaluate"]
    assert len(service.repo.list()) == 1


def test_identical_prompts_in_sequential_turns_are_distinct(tmp_path):
    service, probe = setup(tmp_path)
    for second in [0, 2]:
        run(handle(hook(second=second), service))
        run(handle(hook("AfterAgent", second+1), service))
    assert len(service.repo.list()) == 2
    assert probe.called == ["pre", "evaluate", "pre", "evaluate"]


@pytest.mark.parametrize("case", ["orphan", "mismatch", "overlap", "late", "retry"])
def test_ambiguous_or_retry_hooks_do_not_evaluate_wrong_answer(tmp_path, case):
    service, probe = setup(tmp_path)
    if case != "orphan":
        run(handle(hook(second=3), service))
    if case == "overlap":
        run(handle(hook(second=4), service))
    payload = hook("AfterAgent", 5, prompt="Other" if case == "mismatch" else "Compare cost")
    if case == "late":
        payload["timestamp"] = "2026-10-13T12:00:02Z"
    if case == "retry":
        payload["stop_hook_active"] = True
    result = run(handle(payload, service))
    assert result["decision"] == "allow"
    assert "evaluate" not in probe.called
    assert all(s.answer is None for s in service.repo.list())


def test_sessions_are_independent(tmp_path):
    service, probe = setup(tmp_path)
    for name in ["one", "two"]:
        run(handle(hook(session=name), service))
    for name in ["two", "one"]:
        run(handle(hook("AfterAgent", 1, session=name), service))
    assert len(service.repo.list()) == 2
    assert all(s.post for s in service.repo.list())


@pytest.mark.parametrize("fail", ["pre", "evaluate"])
def test_provider_failure_preserves_request_and_answer(tmp_path, fail):
    service, probe = setup(tmp_path, fail=fail)
    run(handle(hook(), service))
    result = run(handle(hook("AfterAgent", 1), service))
    s = service.repo.list()[0]
    assert s.current_request == "Compare cost" and s.answer
    assert s.failure and not s.terminal and s.post is None
    assert result["decision"] == "allow"
    assert "sensitive" not in result["systemMessage"]
    assert service.repo.trace(s.interaction_id)


def test_timeout_fails_open_without_false_success(tmp_path):
    service, probe = setup(tmp_path, delay=.03)
    service.timeout = .001
    output = run(handle(hook(), service))
    assert output["decision"] == "allow"
    s = service.repo.list()[0]
    assert s.failure and s.pre is None and s.pending_operation is None


def test_interrupted_receipt_does_not_launch_duplicate(tmp_path):
    from app.adapters.gemini.session_store import SessionStore
    service, probe = setup(tmp_path)
    SessionStore(service.repo).reserve(HookInput.model_validate(hook()))
    result = run(handle(hook(), service))
    assert "already claimed" in result["systemMessage"]
    assert probe.called == []


def test_manual_repair_requires_explicit_action_and_preserves_uncertainty(tmp_path):
    service, probe = setup(tmp_path, status="needs_review")
    run(handle(hook(), service)); run(handle(hook("AfterAgent", 1), service))
    s = service.repo.list()[0]
    with pytest.raises(ValueError):
        run(service.repair(s.interaction_id))
    assert service.repo.get(s.interaction_id).next is None and probe.called == ["pre", "evaluate"]
    repaired = run(service.repair(s.interaction_id, [s.intent.requirements[0].requirement_id]))
    assert repaired.next and repaired.followup_answer is None
    assert repaired.approved_uncertainty == [s.intent.requirements[0].requirement_id]
    assert repaired.post.assessments[0].status == "needs_review"
    assert "not sent" in render(repaired)


@pytest.mark.parametrize("payload", [{}, {"hook_event_name": "BeforeModel"}, {**hook(), "timestamp": "bad"}])
def test_bad_protocol_never_calls_provider(tmp_path, payload):
    service, probe = setup(tmp_path)
    assert run(handle(payload, service))["decision"] == "allow"
    assert not probe.called


def test_transport_json_is_safe_without_configuration(tmp_path):
    env = dict(os.environ, PICKYLENS_ENV="test", OPENAI_API_KEY="", PICKYLENS_GEMINI_DB_PATH=str(tmp_path / "transport.sqlite3"))
    result = subprocess.run(["node", "extensions/pickylens/bridge.cjs"], input=json.dumps(hook()),
                            text=True, capture_output=True, env=env, timeout=10)
    output = json.loads(result.stdout)
    assert result.returncode == 0 and output["decision"] == "allow"
    assert "unavailable" in output["systemMessage"]
    assert "OPENAI" not in output["systemMessage"]


def test_extension_contract():
    data = json.loads(Path("extensions/pickylens/hooks/hooks.json").read_text())
    assert set(data["hooks"]) == {"BeforeAgent", "AfterAgent"}
    for items in data["hooks"].values():
        assert len(items) == 1 and len(items[0]["hooks"]) == 1
        assert items[0]["hooks"][0]["timeout"] == 55000


def test_complete_answer_cannot_start_repair_or_change_terminal_state(tmp_path):
    service, probe = setup(tmp_path)
    run(handle(hook(), service)); run(handle(hook("AfterAgent", 1), service))
    saved = service.repo.list()[0]
    with pytest.raises(ValueError):
        run(service.repair(saved.interaction_id))
    assert service.repo.get(saved.interaction_id) == saved
    assert probe.called == ["pre", "evaluate"]


def test_manual_show_works_without_provider_configuration(tmp_path):
    service, probe = setup(tmp_path)
    run(handle(hook(), service)); run(handle(hook("AfterAgent", 1), service))
    saved = service.repo.list()[0]
    env = dict(os.environ, PICKYLENS_ENV="test", OPENAI_API_KEY="",
               PICKYLENS_GEMINI_DB_PATH=service.repo.path)
    result = subprocess.run([sys.executable, "-m", "app.adapters.gemini", "show", "--interaction",
                             saved.interaction_id], env=env, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0
    assert "No follow-up needed" in result.stdout
    assert saved.interaction_id in result.stdout
    assert service.repo.get(saved.interaction_id) == saved


def test_concurrent_duplicate_before_runs_one_review(tmp_path):
    service, probe = setup(tmp_path, delay=.02)
    async def exercise():
        return await asyncio.gather(handle(hook(), service), handle(hook(), service))
    results = run(exercise())
    assert probe.called == ["pre"]
    assert any("already claimed" in r["systemMessage"] for r in results)
    assert len(service.repo.list()) == 1


def test_empty_external_answer_never_becomes_success(tmp_path):
    service, probe = setup(tmp_path)
    run(handle(hook(), service))
    payload = hook("AfterAgent", 1); payload["prompt_response"] = ""
    run(handle(payload, service))
    saved = service.repo.list()[0]
    assert saved.answer.text == "" and saved.post is None and saved.failure
    assert probe.called == ["pre"]


def test_late_service_result_is_trace_only_after_supersession(tmp_path):
    from app.core.contracts import uid
    service, probe = setup(tmp_path, delay=.02)
    async def exercise():
        task = asyncio.create_task(service.request("Compare cost", "superseded"))
        await asyncio.sleep(.005)
        snapshot = service.repo.get("superseded")
        snapshot.pending_operation = None
        snapshot.lifecycle_status = "Interrupted"
        service.repo.save(snapshot, "manual_stop", uid(), snapshot.revision)
        await task
    run(exercise())
    saved = service.repo.get("superseded")
    assert saved.pre is None and saved.lifecycle_status == "Interrupted"
    assert service.repo.trace("superseded")[-1]["type"] == "superseded_result"
    assert service.repo.trace("superseded")[-1]["superseded"].pre


@pytest.mark.parametrize("with_answer", [False, True])
def test_manual_review_entry_point_uses_shared_services(tmp_path, monkeypatch, capsys, with_answer):
    from app.adapters.gemini import __main__ as cli
    probe = Probe()
    request = tmp_path / "request.txt"; request.write_text("Compare cost", encoding="utf-8")
    answer = tmp_path / "answer.txt"; answer.write_text("A costs 5; B costs 8.", encoding="utf-8")
    args = ["pickylens", "review", "--request-file", str(request)]
    if with_answer:
        args += ["--answer-file", str(answer)]
    monkeypatch.setattr(sys, "argv", args)
    monkeypatch.setattr(cli, "ConfiguredProvider", lambda: probe)
    monkeypatch.setenv("PICKYLENS_GEMINI_DB_PATH", str(tmp_path / "manual.sqlite3"))
    run(cli.main())
    assert probe.called == (["pre", "evaluate"] if with_answer else ["pre"])
    output = capsys.readouterr().out
    assert "Record:" in output
    assert ("No follow-up needed" in output) == with_answer
