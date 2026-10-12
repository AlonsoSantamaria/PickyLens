# Slice 2 live verification

Initial authorized run: three live calls, no automatic retries. Requested and returned model: gpt-5.6-sol; reasoning effort: low; store: false.

| Call | Purpose | Returned model | Input tokens | Output tokens | Total tokens |
|---|---|---|---:|---:|---:|
| 1 | pre | gpt-5.6-sol | 500 | 4236 | 4736 |
| 2 | answer | gpt-5.6-sol | 165 | 1611 | 1776 |
| 3 | post | gpt-5.6-sol | 2753 | 2187 | 4940 |

Total: 3,418 input tokens, 8,034 output tokens, 11,452 total tokens. Provider-reported reasoning tokens: 100 for PRE, 191 for the first answer, 0 for POST. POST also reports 2,750 cache-write tokens. These figures are recorded usage, not a cost calculation.

PRE and POST returned typed Structured Outputs. The first answer was generated from the original consultant scenario with no instruction to omit requirements. No PRE clarification was silently accepted; this verification evaluated the original eight scenario requirements without adding model-proposed decisions. The PRE proposal is retained separately.

POST returned 8 Complete, 0 Partial, 0 Missing, 0 Needs review. Core validation passed requirement coverage, exact requirement text, response references, and quoted-excerpt checks. Manual inspection found comparison, cost, timeline, risk for both alternatives, recommendation/reasoning, assumptions/uncertainties, questions before acting, and executive summary. The answer includes unnecessary context and an unsupported memo date, but these do not establish an omission of the eight requested deliverables.

No suitable omission fixture was captured. NEXT, follow-up, and VERIFY were not run because no repairable gap was identified. No additional capture was attempted. The original response and exact inputs, timestamps, response IDs, requested/returned model, effort, status, and usage remain under ignored work/live-verification/. No synthetic content was substituted and no replay fixture was published.

Configuration: project-local .env loads for development, process variables override it, and production disables repository dotenv loading. VESTA is documented to use a protected systemd EnvironmentFile outside the checkout. Secret values were not printed, committed, or copied into reports.

Verification: 19 deterministic tests passed, including dotenv precedence and production isolation. Live model calls are outside the test suite.

Slice 2 remains incomplete. A decision on a further genuine capture or another existing real response is needed before completing the omission-based replay demonstration. The current three-call ledger must be inspected before any later authorized attempt.


## Final authorized capture batch

Exactly four additional calls, two independent answers and one POST per answer. No PRE rerun, prompt modification, omitted-requirement instruction, automatic retry, or further capture. Both answer requests were checked for exact equality with the original saved first-response request. The identical saved intent and requirement IDs were reused.

| Call | Purpose | Model | Input tokens | Output tokens | Total tokens |
|---|---|---|---:|---:|---:|
| 4 | answer | gpt-5.6-sol | 165 | 1538 | 1703 |
| 5 | post | gpt-5.6-sol | 2792 | 2387 | 5179 |
| 6 | answer | gpt-5.6-sol | 165 | 1550 | 1715 |
| 7 | post | gpt-5.6-sol | 2670 | 2250 | 4920 |

Additional usage: 5,792 input, 7,725 output, 13,517 total tokens.
Cumulative usage across seven calls: 9,210 input, 15,759 output, 24,969 total tokens. Requested reasoning effort remained low. Full provider usage details remain in the original call ledger.

Attempt 1: all eight requirements Complete. Attempt 2: all eight requirements Complete. Both retained all requested deliverable elements on manual inspection. No genuine omission fixture was published. The original successful response and provenance remain intact alongside both new captures under ignored work/live-verification/.

Manual evaluator limitation: the first additional answer says a $7,800 three-year premium in its executive summary and shows $17,000 for Option B in its table, then corrects those figures elsewhere to $11,400 and $20,600. POST nevertheless marked cost Complete. This is an inconsistency/assessment-quality finding, not an invented omission; preserve it as evaluation evidence. Do not silently redefine the replay requirement around this result.

Current deterministic tests: 19 passing. Slice 2 remains incomplete. Further capture requires explicit authorization. A decision on the omission-based fixture is required; no NEXT or VERIFY live calls have been made. Gemini CLI Extension v0.1 is recorded only as a deferred stretch goal in checklist.md.


## Authorized material-defect amendment and final POST verification

The learner authorized broadening the fixture criterion from omission to a genuine material quality defect (omission, contradiction, inconsistency, or unresolved uncertainty), retaining unchanged capture/provenance and dynamic assessment. Scope, PRD, specification and their visual companions remain approved with this narrow amendment. No additional first response was generated.

One additional live POST call (cumulative call 8), gpt-5.6-sol / low, evaluated stored final-batch Attempt 1 with generic consistency guidance. Result: 4 Complete, 4 Partial, 0 Missing, 0 Needs review. Partial requirements: concise comparison, costs, recommendation/reasoning, and executive summary. Both conflicting statements are retained as exact evidence excerpts shown in expandable requirement rows.

- Option B three-year total: comparison table $17,000 versus footnote $20,600, calculated from $8,000 + 36 x $350.
- Executive summary: additional $7,800 over three years versus rationale's $11,400 three-year premium; $7,800 is the first-year premium.

A corrective follow-up can reconcile the affected table, summary and rationale without repeating the entire memo. NEXT receives the dynamically assessed Partial requirements and conflicting evidence. Its generic instruction requests narrow corrections; VERIFY can accept explicit superseding corrections while preserving the original trace. Live NEXT/follow-up/VERIFY were not executed under this call limit; their shared pipeline and routing were tested with deterministic stubs. No live repair success is claimed.

Call 8 usage: 3,017 input, 3,852 output (218 reasoning), 6,869 total tokens. Cumulative eight calls: 12,227 input, 19,611 output, 31,838 total tokens. Full local raw responses, requests, timing, usage, and earlier successful captures remain in ignored work/live-verification. The runtime versioned fixture includes original capture provenance, no assessments, and a SHA-256 hash. Its text was checked against raw provider response 4, byte-for-byte at the decoded text level.

Verification: 29 deterministic tests pass, covering multiple synthetic numeric, timeline and logical contradictions; uncertain scope; invalid quotations; both-claim evidence; canonical structured compatibility; replay-only first-answer replacement; mode confirmation/intent preservation; and complete repair pipeline/persistence. Uvicorn workspace and History HTTP checks return 200 without model calls. Existing stage recovery and earlier-request revision remain Slice 3 work.
