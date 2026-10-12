---
doc: post-build-refinement
status: complete
---

# Public PickyLens uses live AI

This separately authorized refinement follows the formally completed 5-build milestone (3f1c8b6 / fefd798). It does not reopen or rewrite scope, PRD, spec, checklist, prior app map, or build evidence. For the current public experience, this amendment supersedes the earlier Replay-default presentation only.

## Authorized behavior

Normal workspace and API use live AI only. No normal mode selector, canonical Replay approval, or synthetic fallback. Missing configuration is explicit. A complete first answer is a successful ending; normal four-state assessments, uncertainty approval, targeted repair and verification remain unchanged. The final approved workbench and responsive orientation are preserved.

Internal Replay and deterministic providers remain available through development runners. Their fixtures, provenance, integrity checks and regressions are retained. Internal records are excluded from normal public History without deletion; this is not an access-control or multi-user feature. Deployment still needs the previously planned reverse-proxy protection.

## Observability

Typed per-call records are attached to the operation using task-local context, then persisted with the existing snapshot/event transaction. They include provider/model, purpose, operation/response IDs, time, duration, available input/output/reasoning/total tokens and outcome. Late results contribute usage without becoming current task results. Retries get separate call records; duplicate operation delivery does not add a call. Existing snapshots load with an empty call list; historical usage is not invented.

The internal read-only report derives PRE outcome, POST counts, detected repairable issues, NEXT need/execution, VERIFY counts and total recorded attempts. Needs review stays separate. Usage totals sum known values and expose coverage. Calls lost on process termination before persistence may have unknown usage; this POC does not claim provider billing reconciliation.

## Future considerations — not implemented

Bounded Judge Pass access, session/account quotas, rate limits, fair-use credits, BYOK, lower-cost routing, and host-native inference belong at provider/orchestration and deployment boundaries. They must preserve approved intent, evidence, and traceability. No accounts, billing, quota system, alternative provider, or Gemini adapter is added here.

## Verification

54 deterministic tests passed, including the unchanged Replay/compatibility/contradiction regressions. New tests cover live-only UI/API behavior, preservation but exclusion of internal records, clear unavailable configuration, SDK usage extraction without network calls, failure/retry/idempotency/restart metadata, and late-call usage without stale state activation. JavaScript syntax, Python compilation and Git whitespace checks passed.

Browser checks confirmed the normal new-case layout has no selector or Replay banner, desktop and 390px layouts have no horizontal overflow, and the real completed interaction has evidence and no Resume. An isolated deterministic public-layout harness verified PRE, original approval, answer, pause/reload/resume, POST, targeted follow-up and VERIFY; compact sticky orientation remains aligned while scrolling. Browser logs contained no warnings/errors. This harness is not live evidence.

## Single bounded live validation

Exactly three additional calls used OpenAI gpt-5.6-sol with low reasoning effort. Same normal consultant scenario; the original request was approved without silently accepting PRE changes. No prompt weakened, defect manufactured, repeated capture, or automatic retry. PRE was Amber; POST found all eight approved requirements Complete. The interaction ended as Complete after first response. NEXT, follow-up and VERIFY were correctly not performed; three unused authorized calls were not spent.

| Purpose | Input tokens | Output tokens | Reasoning tokens* | Total tokens | Duration |
|---|---:|---:|---:|---:|---:|
| PRE | 499 | 1271 | 136 | 1770 | 12.76s |
| ANSWER | 165 | 1527 | 112 | 1692 | 22.78s |
| POST | 3105 | 2629 | 95 | 5734 | 22.32s |
| Total | 3,769 | 5,427 | 343 | 9,196 | 57.86s |

*Reasoning tokens are included in output tokens, not additional tokens. Duration is summed provider-call wall time, not total user session time.

Evidence is preserved locally under ignored work/public-live-verification/: call ledger with exact requests, full raw responses, final snapshot, SQLite interaction/event trace, and engineering report. Interaction ID: 8ae8f45d-a934-4c58-8cdb-0dda1f6ba6d0. Each call has a provider response ID and usage metadata. Existing eight-call build evidence remains unchanged; this batch brings cumulative known calls to eleven, without extending any authorization.

## Product observations and limits

PRE usefully identified undefined priorities, absent operational-benefit data, missing comparison horizon and irrelevant background. POST supplied per-requirement evidence and correctly avoided an unnecessary repair. Manual inspection confirmed the stated first-year/three-year cost arithmetic and incremental costs. No clear material contradiction or false-positive defect was observed in this one response.

However, PRE produced five findings and six optional clarifications, a potentially heavy interaction for a lightweight reviewer. The memo retained unnecessary branding/local-history suggestions; POST still marked the requirements Complete without flagging that excess. This is an evaluator limitation, not evidence of perfect output quality. Requirement extraction and semantic judgments remain fallible. This run supports useful supervision but does not establish that users never need to supervise the evaluator. The answer and reviews use separate calls to the same model, not an independent model family.

Live repair/VERIFY was not exercised because no repairable issue arose; its orchestration remains verified deterministically. Usage can be unknown after a process/network failure before persistence; historical usage is not backfilled. One shared History and one process per SQLite instance remain. The public deployment must retain controlled proxy access; no billing, quotas, Judge Pass, BYOK, alternative routing, Gemini or 6-ship implementation was started.

This bounded post-build refinement is complete. The completed 5-build record and approved planning artifacts are unchanged.
