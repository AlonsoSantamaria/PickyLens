---
doc: gemini-extension-plan
status: approved
baseline: aeb5c6a
---

# PickyLens Gemini CLI Extension v0.1

Architecture proposal researched 2026-10-12. No implementation, installation, authentication changes, or live model calls were made. This is a separate stretch milestone; completed 5-build, Live Web, approved planning artifacts, Replay fixture, provenance and test evidence remain unchanged. Do not start 6-ship.

## Recommended minimum

Use a local Gemini CLI extension with two command hooks and a manual Python adapter entry point. Gemini produces the actual answer in its normal session. PickyLens imports that answer and uses its existing provider abstraction and evaluation services to review it. No web server, VESTA deployment, MCP daemon, new AI SDK, or duplicated evaluation logic is needed.

The initial supported demonstration is a self-contained text request and Gemini's final textual answer. Evaluating filesystem changes, tool side effects, attachments or implicit multi-turn intent is not claimed. Missing context produces an explicit limitation or Needs review, never invented intent.

## Official interfaces and their limits

- An extension uses `gemini-extension.json`; command hooks are registered in `hooks/hooks.json`. Extension settings can declare forwarded environment variables; do not assume arbitrary parent variables survive environment sanitization. [Extension reference](https://geminicli.com/docs/extensions/reference/).
- BeforeAgent provides the request; AfterAgent provides the request and final response. Hooks exchange JSON through stdin/stdout. `systemMessage` can display advisory findings. AfterAgent denial can cause a corrective retry: v0.1 must never use denial for quality findings. Do not inject `additionalContext`, replace the request, or clear context. [Hook reference](https://geminicli.com/docs/hooks/reference/).
- Hooks run synchronously, so external evaluation adds waiting time even when its outcome is advisory. Bounded failure must visibly report review unavailable while leaving Gemini usable. [Hooks overview](https://geminicli.com/docs/hooks/).
- Manual shell passthrough (`!command`) executes a local command and displays its output inside Gemini CLI. This provides a manual entry point without asking Gemini to paraphrase the result. [Command reference](https://geminicli.com/docs/reference/commands/).
- TOML slash commands are prompt templates. Shell output injection feeds the model, rather than providing an ordinary plugin command handler. A future `/pickylens` wrapper would need explicit extra-turn and recursion handling. [Custom commands](https://geminicli.com/docs/cli/custom-commands/).

These are documentation-level findings. Gemini was not discoverable on this shell's PATH; this does not prove it is absent. Installed version, hook rendering and local runtime behavior must be checked before implementation is considered validated.

## Host-native inference: what is actually available

| Route | Current evidence | Implication |
| --- | --- | --- |
| Existing active session through BeforeAgent/AfterAgent | No inference callback is documented in the hook protocol. | Cannot simply ask the suspended host model to execute PickyLens evaluation from a hook. |
| Manual prompt or custom slash command | Uses the host model in its conversation. | Can request self-review today, but alone does not execute our typed, persisted PickyLens core workflow. |
| Local subagent | Host-managed delegated inference exists, with isolated context and model inheritance/configuration. | Potential host-native evaluator, but delegation and a validated core bridge are additional architecture, not a hook callback. |
| Separate headless Gemini process | Can reuse cached CLI authentication and return a JSON envelope. | Technically feasible alternative provider without an OpenAI key; a separate invocation, not access to the current conversation. |
| MCP sampling | No supported sampling route was established in the inspected Gemini MCP documentation/client source. | Do not assume generic MCP sampling availability implies Gemini implements it. |

Sources: [subagents](https://geminicli.com/docs/core/subagents/), [headless mode](https://geminicli.com/docs/cli/headless/), [authentication](https://geminicli.com/docs/get-started/authentication/), [MCP documentation](https://geminicli.com/docs/tools/mcp-server/), [inspected client source](https://raw.githubusercontent.com/google-gemini/gemini-cli/main/packages/core/src/tools/mcp-client.ts). The source reference follows main and is not a pinned installed release.

A headless-provider experiment is possible later. It needs explicit context transfer, hooks/reentrancy isolation, restricted tools, timeout/usage handling and local schema validation. Headless JSON output wraps response text; it does not establish arbitrary Pydantic schema enforcement. Cached authentication does not mean zero cost, unlimited quota, or shared active-session context. Never extract or copy OAuth credentials. None of these alternatives is being implemented in this planning task.

## Proposed files

```text
extensions/pickylens/
  gemini-extension.json
  hooks/hooks.json
  bridge.cjs
  README.md
app/adapters/gemini/
  __main__.py
  protocol.py
  session_store.py
  presentation.py
app/services/host_review.py
tests/test_host_review.py
tests/test_gemini_adapter.py
tests/fixtures/gemini_hooks/
```

The tiny dependency-free Node bridge launches the configured existing Python interpreter and forwards JSON. It contains no product judgments. Gemini payload parsing, correlation and output formatting stay under adapters. `host_review.py` is host-neutral orchestration for externally supplied requests/answers. Reuse `app/core/pre.py`, `evaluation.py`, typed contracts, provider abstraction, telemetry and repository transactions. Reuse `next.py` only for an explicit manual repair-draft request.

Do not import the web application's startup/recovery lifecycle on every hook invocation. Do not route Gemini answers through a fake answer-generation provider. Any necessary shared contract extension must be backward-compatible and covered by existing web regressions.

## Proposed interaction flow and human control

1. BeforeAgent captures the exact submitted request, records an adapter interaction, and runs request review. Display concise human-language findings. No clarification answer is accepted automatically and no improved prompt is silently sent.
2. Gemini continues with the unchanged request. Advisory mode does not provide an interactive pause-and-resume approval dialog. A warning therefore advises rather than guarantees intervention before generation; manual preflight is available when the user wants to review before submitting.
3. AfterAgent imports the actual final answer and checks it against the captured request and extracted requirements. Preserve the four states, evidence and uncertainty.
4. If all assessable requirements are Complete, say the answer meets the reviewed requirements and stop. Partial/Missing findings offer a manual targeted repair draft. Needs review offers inspection/clarification, not automatic repair. No second Gemini call is triggered by findings.
5. The user may manually ask for review or a repair draft and decides whether to submit anything to Gemini. A repair draft is not automatically sent or claimed verified. Automatic cross-turn repair tracking is outside this minimum proposal.

Intent approval needs explicit agreement before coding: submitting text to Gemini authorizes that text as the evaluation target; it does not mean the user personally approved every model-extracted requirement. Preserve this provenance distinction. Extracted requirements are a traceable interpretation, not permission to change intent. Ambiguous or context-dependent requirements remain uncertain. Suggestions become authoritative only through explicit user acceptance or a newly submitted request. Do not fabricate the web UI's approval action.

## Manual invocation proposal

Provide one entry point, `python -m app.adapters.gemini`, available in the terminal and via Gemini shell passthrough. Proposed subcommands: `review` with explicit request/answer files or a specific saved interaction, `show` for existing results, and `draft-repair` for an explicit request to generate a follow-up. The latter never sends it. File-based input avoids putting long or sensitive text into shell arguments.

An illustrative invocation from the repository is `!.venv\Scripts\python.exe -m app.adapters.gemini show --interaction <id>`. This is a planned command, not implemented. Explicit IDs avoid selecting the wrong session when several terminals are open. Manual review works when automatic hooks are disabled. A conventional `/pickylens` slash command is an alternative requiring a separate decision, because its prompt-template semantics add a host-model turn.

## Persistence, failure and correlation

Use a separate ignored adapter SQLite database with the existing snapshot/event transaction conventions; do not mix experimental host records into normal web History. Preserve request, extracted requirements, intent provenance, response, evidence, failure and review-call telemetry. Keep Gemini session identifiers and ordering metadata in adapter-owned storage.

The documented common hook fields do not guarantee a unique turn ID. Correlate session, working directory, transcript reference and a local ordered turn record; validate request matching. Hashing the prompt alone must not merge two legitimate identical requests. Test duplicate delivery, concurrent sessions, orphan AfterAgent and interrupted hooks. If correlation is ambiguous, retain evidence and report unavailable rather than attaching an answer to the wrong intent.

Use bounded execution, per-session coordination, operation IDs and expected revisions. Late results remain traceable but cannot replace newer canonical state. Validate all incoming/outgoing payloads. Keep stdout exclusively protocol JSON, diagnostics on stderr, and prompts out of shell interpolation. Never turn review errors into success or automatic retries. Host token usage/model metadata is unknown unless actually supplied; evaluation telemetry must not be presented as Gemini's usage.

## Authentication and runtime

Gemini retains its own login and permissions. Proposed v0.1 PickyLens reviews use the existing externally configured OpenAI provider, normally one PRE and one POST call per supported turn. A manual repair draft adds a call only when requested. This sends the reviewed request/answer to OpenAI and adds latency; it is a decision for approval, not a newly granted call budget.

Declare required extension settings explicitly and use the project's existing secure environment loading: process configuration takes precedence over local development `.env`. Do not rely on arbitrary host environment inheritance or place keys in extension JSON. Use the existing Python environment and Gemini's Node runtime; no reinstall is planned. Confirm executable location/version first. Linking an extension changes Gemini's user configuration and must be a deliberate later setup action. No deployment changes are needed.

## Smallest build plan after approval

1. Verify installed CLI version and extension protocol locally without inference. Build a thin deterministic request/answer hook demonstration plus manual entry point. Confirm message visibility, no injected context and no retry behavior.
2. Connect shared PRE/POST services and external-answer capture with deterministic providers and a separate durable trace. Demonstrate complete, partial, missing, uncertain and inconsistent answers; prove human intent is unchanged.
3. Add bounded failures, duplicate/concurrent event handling, manual repair drafting and regression coverage. Run the full existing suite and fixture-integrity checks; review the CLI experience hands-on.
4. Only with a fresh, stated live-call budget, validate a real Gemini turn with real reviews, record provenance/usage, then stop for hands-on approval. No live calls are authorized by this document.

## Decisions before coding

- Approve external OpenAI review for v0.1 while Gemini generates the answer, or choose a separately scoped host-native provider experiment first.
- Approve advisory continuation and submitted-request intent provenance, with no automatic acceptance of PRE suggestions.
- Approve the shell-passthrough manual invocation and standalone textual-turn boundary, or require a slash-command/context-aware variant before implementation.
- Locate the existing Gemini CLI executable/version, if installed. Installation or authentication is not assumed or undertaken.

## Planning verification

Only these new planning records are written. No code, original planning status, replay data or historical evidence is changed. No automated application tests are needed for documentation-only changes. Whitespace and repository diff checks must pass before presenting the plan. This document remains draft pending the user's decisions.

## Approved implementation baseline — 2026-10-13

The user approved external OpenAI reviews, advisory continuation, a thin adapter, and separate experimental host records. Gemini CLI 0.63.0 is installed at `C:\Users\alons\AppData\Roaming\npm\gemini.cmd` and authenticated by the user. Use that installation without reinstalling tooling. Deterministic implementation is authorized; live inference remains gated on a separate call budget.

Shell passthrough is a technical fallback only, not approved as final judge-facing or commercial manual UX. Investigate a natural/native manual invocation later, without expanding this milestone into a command-system project. The decisions above are historical proposal text; this approval resolves them.
