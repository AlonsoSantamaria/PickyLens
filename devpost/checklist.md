---
doc: checklist
status: approved
---

# PickyLens Build Checklist

Build mode: fast — selected by the learner; mechanical verification remains mandatory. Pause for early hands-on feedback and final review. Build order approved; Slice 1 hands-on feedback accepted. Continue in Fast mode with verification.

## Slices

- [x] **1. Review a request and verify a targeted repair end to end**
  Becomes usable: A local two-column workspace where the user starts PRE, reviews extracted requirements and clarifications, approves intent, obtains a deterministic stub answer in Slice 1, runs POST, reviews and sends a minimal follow-up, and verifies the combined result. Meaningful steps survive restart, and saved interactions are inspectable through a minimal list/detail.
  Why now: Proves the unique quality loop early, including human ownership and evidence, instead of building scaffolding around an absent kernel. Bootstrap, persistence, and the provider adapter support this usable path within the slice.
  PRD ref: `prd.md > The Core Journey`, `PRE Review and Approved Intent`, `POST Evidence Review`, `NEXT Follow-Up and VERIFY`, `Minimal Interaction History`, `Look and Feel`
  Spec ref: `spec.md > Stack`, `Where It Runs and How Someone Tries It`, `Look and Feel`, `Components`, `Data Model`, `HTTP Contracts`, `File Structure`, `External Services and Dependencies`
  Build: Create the project-local Python environment using the existing interpreter, pin application/test dependencies, preserve Git ignore safeguards, and implement the neutral provider boundary and injected deterministic development stub, typed intent/evidence services (real OpenAI adapter deferred to slice 2), transactional snapshot/event persistence, and a working server-rendered workspace plus minimal History. For Slice 1 only, provide an explicitly labeled development-only stub runner with no live calls; do not represent it as Replay Demo or captured model output. Enforce manual approval, stable requirement IDs, evidence references, four-status results, explicit follow-up sending, and persistence beginning only at first PRE. Keep Replay acquisition unavailable with an honest explanation until a genuine compatible fixture exists in slice 2.
  Verify (mechanical): Run focused pytest tests with a test-only provider through FastAPI TestClient for the full PRE/approval/answer/POST/NEXT/follow-up/VERIFY journey, evidence validation, no History before PRE, first-PRE failure preservation, transaction rollback and reopen persistence; defer concurrency/retry robustness to slice 3. Start Uvicorn and verify workspace/History pages over HTTP. Any real adapter smoke check is separately announced with its purpose and expected call count before execution.
  Learner check: Start the documented devtools.stub_app server and open http://127.0.0.1:8000/. Use the prefilled scenario, review, choose Lowest upfront cost, save the clarification, approve the improved prompt, generate the answer, run POST, generate/edit/send the follow-up, then VERIFY and inspect History. Expect 8 Complete/1 Missing before repair and 9 Complete/0 Missing after, including the accepted priority. Report what you notice and what you would change before the remaining slices.
  Commit: `Build persistent PickyLens interaction quality loop`

- [x] **2. Run the honest, repeatable Replay Demo beside the live path**
  Becomes usable: The default Replay Demo uses a documented genuine first response tied to canonical structured intent; all reviews, repair generation, the follow-up answer, and verification still run dynamically. Live Model remains available.
  Why now: The working loop can now demonstrate a real material defect repeatably without manipulating the model or hard-coding assessments.
  PRD ref: `prd.md > Replay Demo and Live Model`, `Switching Modes During Active Work`, `The Core Journey`
  Spec ref: `spec.md > Replay Scenario and Compatibility`, `Provider Boundary and OpenAI Adapter`, `Operations, Restart, and Stale Responses`, `HTTP Contracts`
  Build: Capture or select a real unmanipulated consultant answer with a genuine material quality defect, preserve exact provenance in versioned JSON, and bind it to canonical requirements/accepted decisions/constraints. Implement deterministic structured compatibility, conservative uncertainty rejection, reset/live choices, mode-switch confirmation, and superseded response evidence. Never substitute a test stub or fabricated provenance for the real replay fixture. Explain the purpose and expected number of live calls before any capture or semantic smoke run; stop to report account/model-access failures instead of silently changing models.
  Verify (mechanical): Run replay compatibility tests covering equivalent structured intent with superficial wording changes, substantive differences, unmappable requirements, and no compatibility AI call. Verify only the first answer is replaced and subsequent stages use the provider. Run mode-switch route tests preserving PRE/intent and superseding downstream results. Manually inspect real capture provenance and material-defect evidence; use a bounded, announced real-model smoke run to verify API/schema support and dynamic semantic behavior.
  Learner check: Open Replay Demo, follow the canonical scenario, inspect the captured-response label and genuine material defect, then review/edit/send the targeted follow-up and inspect verification. Change material intent and confirm Replay offers reset or Live rather than silently using an unrelated answer.
  Commit: `Add genuine replay fixture and deterministic compatibility`

- [ ] **3. Resume, revise, and recover without stale or misleading results**
  Becomes usable: Active requests can be revised safely, failed work can be retried or paused and resumed, and uncertainty or already-complete answers end honestly without unnecessary repair calls.
  Why now: The demonstrated core is extended across the edge cases that protect traceability and user control, while retaining the same small workspace and History.
  PRD ref: `prd.md > Request Changes and Superseded Results`, `POST Outcomes Without Repairable Gaps`, `Minimal Interaction History`, `Empty Requests and Empty History`, `States and Boundaries`
  Spec ref: `spec.md > Interaction Coordinator and State Rules`, `PRE and Intent Establishment`, `POST and VERIFY Evaluation`, `SQLite Repository and History`, `Operations, Restart, and Stale Responses`, `Important Failure Modes`
  Build: Complete request-edit intent supersession, revised improved-prompt review, Red override confirmation, Needs review resolution/approved questioning, complete-first-response and qualified terminal outcomes, nonterminal Resume, terminal immutability, explicit retry/edit/stop behavior, restart-interrupted operations, optimistic concurrency, stale-result preservation, and append-only event guards. Ensure generated/edited follow-up drafts and failure/recovery states persist. No branching, background retries, or additional History features.
  Verify (mechanical): Run deterministic transition, repository, evaluation, and route tests for all-complete/no-NEXT, uncertainty-only outcomes, approved uncertainty targets, Red override, changed request versus changed mode, failed stages/retry, interrupted restart, stale revisions/late responses, terminal mutation rejection, read-only History, and saved draft restoration. Verify blank input creates no interaction or findings and empty History has no fake entries.
  Learner check: Pause or fail an interaction, reopen it through History, and resume at the preserved stage. Revise an earlier request and inspect superseded evidence. Confirm terminal records have no Resume and Needs review is never presented as confident success.
  Commit: `Complete interaction recovery uncertainty and supersession rules`

- [ ] **4. Verify the complete local POC and prepare it for final review**
  Becomes usable: The approved flow is runnable from documented local commands, with compact responsive presentation, inspectable evidence, and clear setup/fixture limitations.
  Why now: Checks the assembled user journey after its state rules are complete and prepares an honest hands-on review without starting submission or deployment work.
  PRD ref: `prd.md > Screens and Layout`, `Look and Feel`, `The Core Journey`, `What We're Building`, `Non-Goals`
  Spec ref: `spec.md > Where It Runs and How Someone Tries It`, `Look and Feel`, `Verification Approach`, `Important Failure Modes`, `Decisions and Open Issues`
  Build: Finish responsive/keyboard presentation and evidence reveals, document setup, secret-free environment defaults, fixture provenance, test commands, and local recording. Validate errors and safe model-text rendering. Keep optional VESTA deployment unexecuted until its environment/access arrangements are verified; local operation must stand alone. Make only corrections needed for approved behavior.
  Verify (mechanical): Run the complete focused test suite and start the documented Uvicorn command. Inspect rendered workspace, History, controls, evidence, failure messages, and narrow layout using available authorized browser tooling. Confirm ignored runtime databases/credentials and inspect intended staged diffs before committing. Report any unavailable browser or real-provider verification honestly.
  Learner check: Start the server, freely explore the canonical replay cycle, Live path, awkward inputs, History/resume, and final evidence. Report broken or confusing behavior and confirm readiness only after agreed fixes are retried.
  Commit: `Polish and verify the local PickyLens proof of concept`

Slice 1 implementation evidence: 13 deterministic pytest checks passed. Workspace and History returned HTTP 200 under Uvicorn. A real browser completed PRE, explicit priority acceptance, intent approval, first stub answer, POST (8 Complete/1 Missing), targeted NEXT, edited follow-up send, and VERIFY (9 Complete/0 Missing), with resolved evidence pointing to the follow-up. Read-only terminal History and the saved edited draft were inspected. Desktop two-column and narrow stacked layouts were observed. Zero live model calls were made.

Checkpoint state: Learner approved Slice 1 hands-on review and continuation. No immediate repairs requested. First-use guidance is deferred to final polish.

## Hands-on Checkpoints

- [x] Early usable behavior explored — after slice 1, before slice 2; record actual learner feedback and verified fixes.
- [ ] Final kick-the-tires exploration and feedback completed — after slice 4; cover the integrated quality loop and History without a redundant middle checkpoint.

## Final Review

- [ ] Add lightweight first-use guidance for PRE -> AI -> POST -> NEXT -> VERIFY during final polish: contextual step cues and concise helper text, without a heavy tutorial. Requested after Slice 1; do not interrupt Slice 2.

- [ ] Final review complete — feedback resolved and learner confirms ready to ship

## Code Tour and App Map

- [ ] Learning activity complete — focused investigation of provider independence and evidence validation using actual finished code/tests
- [ ] Optional edit and transfer reflection addressed — offered/declined/already covered/not applicable as appropriate
- [ ] `devpost/app-map.html` generated from finished code, checked, and shown, including a project-grounded practice to reuse

Activity and evidence: Pending final review; use the learner's goal of delegation through specifications and a provider-neutral core.
Route and stops: Pending finished implementation; reference actual code and test locations only.
Edit outcome: Not yet offered.
Reflection: Not yet offered; any personal response belongs only in the ignored learner profile.
Activity mode: Focused alternative for an experienced plan-first user; perform once after final revisions.

## Revisions

- Slice 1 narrowed by the learner to the smallest complete golden path with real SQLite and deterministic provider stubs, including a labeled local stub runner. No live calls in this slice. Retries, supersession, concurrency, and recovery edge cases remain in slice 3. Stop at the early hands-on checkpoint until the learner approves continuing.
- Slice 1 browser verification exposed misencoded JavaScript punctuation; corrected the source and script encoding and verified the rendered reviewer labels. Local-only pytest scratch is created under ignored work/ rather than outside the project. No product or architecture changes.

- Slice 2 started: deterministic canonical-intent comparison and tests added. Integration, provenance capture, and real-provider verification remain incomplete. No API key was available in the execution environment or a project .env file; no live calls made. First-use guidance remains deferred to final polish.

- Local development now loads project-root .env through python-dotenv with process-environment precedence; production ignores repository dotenv and uses the planned external systemd environment file. Secret values remain excluded.
- Slice 2 initial live verification made exactly three calls using gpt-5.6-sol/low: PRE, first answer, POST. All eight original requirements were complete. No suitable omission fixture; stopped before further capture or unnecessary NEXT/VERIFY. See live-verification.md. Nineteen deterministic tests passed. Slice 2 remains unchecked.


## Official Deferred Stretch Goal: PickyLens Gemini CLI Extension v0.1

Objective: demonstrate the same PickyLens Core inside an external AI host workflow.
Target: Gemini CLI extension with BeforeAgent -> PRE, AfterAgent -> POST, and one manual PickyLens command. Reuse approved-intent/evaluation logic without duplicating product logic in the adapter.
Manual control remains available. Automatic PRE/POST is lightweight and advisory. No automatic retry or silent task alteration. The human controls clarification, repair, and follow-up.
Gemini is a host adapter; no Gemini-specific assumptions enter the core. Hook feasibility is to be verified when this stretch work is authorized.
Status: officially recorded, deferred, not implemented. Outside the MVP and current Slice 2 work. Finish the approved Slice 2 first.

- Final authorized capture batch exhausted exactly four additional calls (seven cumulative). Both POST outcomes were 8 Complete with no Partial/Missing; no omission fixture obtained. The initial successful capture remains preserved. Manual inspection found a cost inconsistency missed by POST in the first additional answer; documented as an evaluator limitation. No further calls or Gemini implementation. Slice 2 remains incomplete pending the learner decision.


## Slice 2 completion evidence

- Learner authorized the material-quality-defect amendment and one final POST verification, without additional first-response capture.
- Genuine final-batch Attempt 1 integrated unchanged with provenance/integrity hash. POST dynamically detected four Partial requirements affected by conflicting costs, with four Complete.
- 29 deterministic tests pass; real Uvicorn workspace/History HTTP checks pass. Replay replaces only first-answer acquisition; structured compatibility makes no AI call.
- Exactly one additional live POST call; no live NEXT/follow-up/VERIFY in this batch. Those stages were verified deterministically, not claimed as live semantic success.
- Stop after Slice 2 per learner instruction. No Slice 3 or Gemini stretch implementation. Final-polish guidance remains deferred.
