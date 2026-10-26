# PickyLens reliability review

Date: 2026-10-26. Audience: Diana and project owner.
Status: local correction verified deterministically; deployment and live acceptance pending authorization.

## Established findings

The requirements called for a real, reliable application. Model variability is an expected operating condition that the implementation must handle; it is not an explanation that excuses losing an entire review. The confirmed implementation weakness was an unnecessarily brittle boundary between model output and application state, compounded by insufficient diagnostic evidence. Passing deterministic happy-path tests and earlier live examples did not establish coverage of this boundary.

The former evaluator required the model to reproduce intent version, phase, requirement IDs and exact requirement text. It rejected the entire evaluation on a mismatch, missing/duplicate mapping, or invalid evidence. The interaction service then restored the preceding snapshot and displayed a generic stage failure. This could discard otherwise usable assessments after a successful, chargeable provider response. Code inspection and synthetic regression tests establish this failure class; they do not prove which check rejected the historical responses.

### Historical POST evidence

Interaction: `055881db-f3ac-4986-8ee4-867f12402853`. Both provider responses completed; both operations persisted a POST failure without a current POST evaluation. The previously completed answer remained saved. Operation suffixes below omit the anonymous-session namespace; full correlation remains in the existing production records.

| Evidence | First POST | Explicit retry |
|---|---|---|
| Operation suffix | `27bd8c08ceba7079e9dc6e8016214f7144cf506953d937923a5ad31d52a4587a` | `43620dbb12c91b197bb899bc9518cb623ea4c94bd73105e9d570c587bab30c80` |
| Call ID | `4f430e4b-8bad-41fb-a71a-276a037bbf20` | `d984b931-1964-4b4b-b613-fdc668082075` |
| Provider response | `resp_020ac76964e8ad70016adf8762031487d1b78548305ff7554b` | `resp_002a9957b264f629016adf88648ad887d1a741a3691f3d9453` |
| Start UTC | 17:01:21.822027 | 17:05:40.204955 |
| Failure event UTC | 17:02:01.460338 | 17:06:17.428682 |
| Provider duration | 39,623.11 ms | 37,206.04 ms |
| Input / output / total tokens | 3,619 / 4,258 / 7,877 | 3,619 / 3,630 / 7,249 |
| Reasoning tokens, included in output | 190 | 146 |

Provider: OpenAI, `gpt-5.6-sol`, low reasoning. Combined usage: 15,126 tokens. These were two separate recorded operations, not evidence of automatic retry.

The raw structured judgments and precise rejecting validation codes were not retained. The exact rejecting check for either attempt is therefore **unrecoverable from the surviving evidence**. No original-response reproduction is claimed. The completed provider calls and downstream failure distinguish this incident from the earlier provider-credit exhaustion. An allowance denial did not cause these two POST failures. No evidence implicates the Markdown/scrolling deployment.

Production records, prior commits, fixture and provenance remain unchanged. Production remains on `896bacf`; this correction has not been deployed.

## Contract correction

| Responsibility | Application now owns | Model supplies |
|---|---|---|
| PRE | Requirement IDs/source and clarification keys | Proposed requirement text, readiness, findings, questions and improved prompt |
| POST / VERIFY | Canonical intent version, phase, IDs and requirement text; fixed requirement slots; answer-index to response-ID mapping | Status, explanation, candidate excerpts, uncertainty and consistency findings |
| NEXT | Authorized target IDs derived from current assessment and explicit uncertainty approval | Follow-up draft text for those targets |

User approval remains the authority for intent. Existing canonical provider interfaces and host service reuse remain intact; wire conversion is separate. No new inference call is added. NEXT text still needs human review: assigning authorized target IDs does not prove that generated prose respects scope.

## Integrity and recovery policy

- Authentication, quota, network, timeout, incomplete/refused output, invalid JSON/top-level structure, or a wholly unmappable response remain fatal. Work is preserved and another call requires explicit retry.
- Missing/duplicate or malformed individual assessments become application-owned **Needs review** placeholders. Valid assessments for other requirements survive.
- Invalid or non-exact excerpts are discarded. Complete without valid evidence becomes Needs review. Unsupported contradiction claims are removed and the affected requirement becomes Needs review.
- Confirmed contradiction findings still require at least two distinct valid excerpts. Uncertain findings remain Needs review. Exact quotation proves source correspondence, not that the model's semantic interpretation is correct.
- Custom providers cannot change canonical text. Wrong phase/version cannot be trusted and conservatively leaves all affected judgments Needs review. Unknown mappings are never attached to a different requirement by guessing.
- VERIFY maps evidence to the supplied first/follow-up answers while preserving canonical requirement identity. Existing stale-result, terminal-state, concurrency and recovery rules remain in force.

Safe typed diagnostics now record failure layer, stage, validation code, sanitized field path and applicable requirement/call/response IDs. Snapshots and event traces preserve these diagnostics alongside known model usage. No raw prompt/output or exception text is added solely for diagnostics. SQLite finalization errors emit a safe journal diagnostic; if storage itself fails, that same database cannot also be relied on to save the diagnostic. The previously saved pending operation remains recoverable.

Provider metadata is still captured and usage settled before local typed/semantic validation. Completed rejected responses retain actual token usage. Unknown usage retains the existing conservative reservation. No budget or access controls were reset or increased.

Private SDK response parsing was replaced with public JSON/Pydantic decoding of the public Responses result, enabling per-requirement validation without losing usage. The pinned SDK's private strict-schema conversion helper is retained: replacing that separately would add unnecessary risk. Its strict output and adapter decoding are covered deterministically.

## Verification

- **144 Python tests passed**, including 36 new reliability regressions.
- **4 Node tests passed**, covering browser worker protocol and Markdown safety/rendering behavior.
- Python compilation and Git whitespace checks passed.
- New tests cover valid/mixed assessments; missing, duplicate and unknown mappings; altered text; wrong phase/version; invalid/paraphrased evidence; unsupported/ambiguous contradictions; missing evidence/uncertainty; malformed, refused, incomplete and ambiguous output; commentary exclusion; auth/quota/timeout/network failures; diagnostic privacy; explicit retry/idempotency; persistence failure; and retained actual usage after rejection.
- An actual OpenAI adapter with simulated transport responses completed PRE → approval → answer → POST → NEXT → follow-up → VERIFY, persisted stable requirement/evidence identities, and made exactly six simulated calls. Existing recovery, access, global-breaker, host and UI regressions also passed.
- **Zero live inference calls. No production deployment, restart, data mutation or allowance changes.** Synthetic mutations are not represented as captured production responses.

## Remaining limits and bounded acceptance proposal

This corrects verified contract and recovery weaknesses; it does not establish perfect semantic judgments or prove live compatibility of the new wire schema. PRE extraction, evidence relevance, contradiction interpretation and generated follow-up scope remain model-dependent and user-reviewable. Provider availability/credits and unknown-usage reservations can still prevent service. A process/database failure can leave pending work requiring explicit recovery.

After separate authorization:

1. Check provider configuration, service health and existing budget capacity read-only. Do not reset/increase limits. Preserve current production as rollback, then deploy the reviewed correction while preserving external configuration and databases.
2. Use one ordinary request through the real Web path: PRE, explicit user approval, answer and POST: **3 provider calls**.
3. If that answer is complete, stop successfully. If genuine repairable gaps exist, and the user approves the draft, run NEXT, follow-up and VERIFY: **at most 3 additional calls**, maximum **6 total**. Do not manufacture gaps, repeat PRE, retry for a better outcome or add uncertainty-resolution calls beyond this budget.
4. Record exact model/effort, IDs, usage, timing, canonical mapping, evidence, final state and diagnostics. Stop on any fatal failure. Keep deterministic repair/VERIFY evidence if the live answer needs no repair.

Authorization is required before deployment/live acceptance. No Gemini or other host generation is needed for this bounded Web acceptance.
