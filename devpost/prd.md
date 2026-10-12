---
doc: prd
status: approved
---

# PickyLens — Product Requirements

An AI interaction quality layer for a management consultant preparing an executive recommendation memo for a small-business owner.

Source: `scope.md > The Unique Kernel`, `Who It's For`, `The Core Loop`, and `The POC Boundary`. Minimal Interaction History is the explicit learner-directed scope amendment in `scope.md > Minimal Interaction History`; that amended scope is approved.

## The Core Journey

1. Open the workspace in Replay Demo, with the canonical management-consultant scenario and an editable, intentionally imperfect request.
2. Deliberately click "Review with PickyLens". This first click creates the Interaction and begins automatic persistence. Read a concise PRE assessment of material issues and provide any needed human decisions.
3. Inspect the improved prompt once required clarifications are resolved. Choose "Use improved prompt", "Edit improved prompt", or "Send original". PRE cannot silently change intent.
4. Obtain the first answer: the transparently labeled captured response in compatible Replay Demo, or a new model response in Live Model.
5. Run POST against the user's approved intent. Inspect Complete, Partial, Missing, and Needs review requirements, explanations, and supporting evidence.
6. If all requirements are Complete, end successfully without an extra AI call. If only Needs review items remain, offer user-led resolution or end with review items. When repairable gaps exist, click "Fix only what's missing" to generate a minimal follow-up for partial and missing requirements. Review or edit it, then explicitly send it to the model.
7. Receive a new follow-up response. VERIFY evaluates both answers together against the approved intent and updates the same requirement list, showing resolved gaps and remaining uncertainty.
8. Inspect the final outcome and evidence. Open the saved interaction through the Interactions page to trace the stages, including any failures or recovery.

Sources: `scope.md > The Core Loop` and `What "Working" Looks Like`; learner's explicit History addition.

## Screens and Layout

### Workspace

At the top: PickyLens, "Quality-check the whole AI interaction.", and a compact Replay Demo / Live Model control. Replay Demo is the initial mode.

The desktop workspace is an approximately 50/50 workbench: left is what the user asks; right is what the AI returns. The left holds the editable original request, request review, clarifications, improved/approved request, and targeted follow-up. The right holds the AI answer, requirement/evidence review, follow-up answer, and verification. The initial right side contains only an honest empty state.

Human-language stages dominate: Review request, AI answer, Check answer, Fix gaps, Confirm. PRE / AI / POST / NEXT / VERIFY may remain secondary labels. When an answer arrives, transfer focus to its heading on the right, cue reading, and place Check this answer beneath the response. Do not require a read confirmation. Keep one primary next action beside the content it acts on. Follow-up generation moves attention left; its response and Verify result action belong on the right. Show actual dynamic before/after counts and unchanged evidence.

First-use guidance briefly explains left=request, right=answer, and PickyLens checks both. On narrow screens stack request/action, answer/review, follow-up prompt, follow-up answer/verification in that order. History retains all information and traceability while using human-language stage labels. This learner-authorized final-review refinement changes presentation only.

### Interactions

One simple page contains a compact list of saved interactions and a read-only detail view for a selected interaction. Each row shows date/time, a short descriptive title automatically derived from the scenario or task, mode, and current/final status. Internal unique IDs need not be prominent; manual renaming is not required. Preserve the original prompt, PRE findings, accepted clarifications, approved prompt and intent, AI responses, POST findings, generated/edited follow-up, and final verification. Failures and recovery remain inspectable.

History detail remains read-only. Nonterminal incomplete, failed, paused, or unresolved-review interactions offer "Resume interaction", which returns to the main workspace with all saved context and completed stages at the last meaningful state. Terminal interactions offer no Resume and cannot be edited or reopened for continued work.

Sources: `scope.md > The Core Loop`, `Inspiration & Identity`; learner's explicit History addition.

## Look and Feel

Refined, calm, precise, slightly editorial, compact without crowding, and suitable for consulting or business work: "serious enough for professional work, friendly enough to use every day."

Use Inter if practical, restrained hierarchy and stronger weights rather than oversized headings. Monospace may appear sparingly for model metadata, IDs, or technical evidence, not the main experience.

Use warm off-white or very light neutral backgrounds, deep ink/navy primary text, and one distinctive cool accent in the indigo/blue-teal range for PickyLens actions and identity. Reserve green, amber, and red primarily for readiness and requirement-status signals.

Avoid heavy gradients, neon AI aesthetics, glassmorphism, decorative dashboards, excessive cards, pervasive chatbot bubbles, and generic SaaS styling. A lens motif is a possible reference, not a selected icon. A reviewer character is only a future possibility, not an MVP requirement.

Source: `scope.md > Inspiration & Identity`, elaborated by the learner's visual direction.

## Features and Behavior

### PRE Review and Approved Intent

The user manually initiates PRE. Show a Green, Amber, or Red readiness state and only material findings, such as missing priorities, ambiguous constraints, contradictions, or unnecessary context. Findings are brief and understandable.

- **Green — Ready:** no material issues likely to affect the result; requirements are clear enough, no important contradictions or essential missing user decisions, and sufficient constraints to proceed. Show "Ready to send." The original request can be sent immediately.
- **Amber — Worth improving:** usable, but an issue could noticeably reduce quality, completeness, or efficiency, such as a useful missing constraint, ambiguous interpretation, unnecessary context, or implied priorities. Show "Usable, but worth improving." Offer improved-prompt acceptance/editing or sending the original.
- **Red — Resolve before sending:** a significant issue, such as contradictory instructions, a critical missing user decision, absent essential information, or an unevaluable deliverable. Show "Important issue before sending." Strongly recommend resolving it, but preserve user control through "Send original anyway" with explicit confirmation.

Sending the original remains possible in every readiness state. A Red override does not silently resolve the issue or turn an unaccepted clarification into approved intent. PickyLens advises rather than permanently blocking the user.

When a finding requires a human decision, show a compact clarification question with suitable selectable options or a short input. Do not invent the answer. Once required clarifications are resolved, show an Improved prompt section and the three prompt choices above. Avoid unsolicited prompt-engineering explanations.

Approved intent comprises the original request's requirements plus material clarifications, constraints, or decisions explicitly accepted during PRE. Unaccepted suggestions cannot silently become evaluation requirements.

Acceptance criteria:
- PRE starts through a deliberate user action, not automatic review.
- Findings concern material issues and required human decisions are not supplied by the reviewer.
- The user can keep the original request in every readiness state or inspect, edit, and accept the improved version.
- Red shows "Send original anyway" and requires explicit confirmation; Green and Amber do not impose this Red-specific override.
- POST verifies accepted intent rather than silently adopted PRE suggestions.

Source: `scope.md > The Core Loop` and `The POC Boundary`.

### Request Changes and Superseded Results

During an active interaction, editing an earlier prompt makes the edited prompt the new current request. Downstream results based on the previous version become stale: preserve them in the interaction trace, clearly mark them superseded, and stop presenting them as current.

Accepted intent from the previous request is no longer current unless it is still explicitly applicable. Return to PRE on the edited request, preserving deliberate manual initiation, and establish a new approved intent before continuing. AI responses, POST findings, NEXT prompts, and VERIFY results tied to the old approved intent are invalid for current-state purposes.

Show a clear message such as: "Your request changed. Previous review results are now outdated and will be preserved in the Interaction history, but they are no longer current."

Acceptance criteria:
- Editing a request during an active interaction returns the current workflow to PRE and requires new review and approved intent.
- Old downstream results remain inspectable as superseded evidence, not current findings or verified success.
- Clarifications from the previous intent cannot silently carry forward unless still explicitly applicable.
- This behavior does not permit editing terminal interactions or read-only History detail.
- No branching interface or version comparison is required for the MVP.

Source: `scope.md > The Core Loop` and the learner's request-change decision.

### Replay Demo and Live Model

Replay Demo is tied to a canonical scenario and its approved intent, not merely its raw prompt text. The captured first response is real, polished, contains a genuine material quality defect, and is transparently documented and labeled.

Only the first response is controlled. PRE, POST, minimal follow-up generation, the follow-up model call, and final verification execute dynamically. Live Model obtains the first response live too; a complete first answer is a valid outcome.

If edits or accepted clarifications materially change the intent so the fixture is unsuitable, do not use it. Explain the mismatch and offer "Reset to the canonical demo scenario" or "Continue in Live Model mode". Minor wording changes may remain compatible; uncertain compatibility is treated as invalid.

Acceptance criteria:
- The initial mode is Replay Demo, and the captured response is identified as replayed.
- A mismatched or uncertain request never silently receives the fixture.
- All stages other than the replayed first response execute dynamically.
- Live Model uses one model configured outside the UI, with no model/provider configuration screens.

Source: `scope.md > What "Working" Looks Like` and `The POC Boundary`.

### Switching Modes During Active Work

Preserve the original request, valid PRE findings, accepted clarifications, approved intent, and user edits supporting that intent. Before the first AI response, changing mode does not require repeating PRE; use the selected mode for the AI step, subject to replay compatibility.

After an AI response exists, warn before switching that current downstream results will become superseded. Preserve the old response and dependent POST findings, NEXT prompt, follow-up responses, and VERIFY results as prior evidence, not the current flow. No branching timeline is required.

Replay Demo -> Live Model preserves approved intent, generates a new live response, and reruns POST onward. Live Model -> Replay Demo first checks approved-intent compatibility with the canonical scenario. If compatible, use the fixture and rerun POST onward. If incompatible or uncertain, do not use it; offer "Reset to the canonical replay scenario" or "Remain in Live Model".

Acceptance criteria:
- A mode change alone does not discard valid request/PRE/intent work or require repeating PRE.
- Before switching after an answer, warn about superseding dependent results.
- Prior evidence remains inspectable but is not shown as current.
- The current flow uses the response associated with the selected mode and a fresh dependent review.
- Live -> Replay never uses an incompatible or uncertain fixture.

Source: `scope.md > The POC Boundary` and the learner's active mode-switch decisions.

### POST Evidence Review

Show actual requirement counts, counting Complete, Partial, Missing, and Needs review separately. Compact rows contain the requirement, its status, a short explanation, and evidence where applicable. Expand a row to inspect the relevant excerpt or location. For missing content, explain what was not found rather than fabricate supporting text.

When evidence is insufficient or ambiguous, use Needs review rather than forcing Complete, Partial, or Missing. Explain why the judgment is uncertain and show relevant evidence or its absence. First check whether the existing interaction resolves the uncertainty. If it does not, offer "Resolve this uncertainty" or "Leave as Needs review". A narrowly targeted AI question may be included in the follow-up only with user approval; Needs review is not automatically treated as missing.

Acceptance criteria:
- Counts reflect the actual evaluation, not fixed example totals; Needs review is counted separately.
- Each requirement is inspectable with an explanation and relevant evidence where available.
- A genuine material quality defect in the compatible replay response can be identified despite polished presentation.

Source: `scope.md > The Unique Kernel`, `The Core Loop`, and `What "Working" Looks Like`.

### POST Outcomes Without Repairable Gaps

If POST finds no Partial or Missing requirements, do not show "Fix only what's missing".

When every requirement is Complete, show the actual counts for all four statuses and "PickyLens verified that all requested requirements are fulfilled." End successfully without generating a follow-up or making another AI call. Evidence remains expandable, and History records "Complete after first response".

When only Complete and Needs review requirements remain, do not mark the interaction Complete or generate an automatic repair prompt. Show actual counts and explain that no repairable gaps were found but some requirements could not be verified confidently. Each uncertain item offers "Resolve uncertainty" or "Leave unresolved". If resolution needs AI information, prepare only a narrowly targeted question and require user approval before sending. The user may end with unresolved items; History records "Completed with review items" rather than full completion.

NEXT exists only when there is useful repair or clarification to perform; do not manufacture it to preserve a fixed sequence.

Acceptance criteria:
- No repair button appears when Partial and Missing counts are both zero.
- All-Complete results end successfully with inspectable evidence and no extra AI call.
- Needs review alone does not imply failure or verified completion, and does not cause an automatic follow-up.
- Ending with unresolved review items preserves them and the qualified History status.

Source: `scope.md > What "Working" Looks Like` and the learner's explicit no-gap outcome decisions.

### NEXT Follow-Up and VERIFY

"Fix only what's missing" generates the smallest useful follow-up targeted at Partial and Missing requirements by default, not a repetition of the entire task. Needs review items are excluded unless the user approves a narrowly targeted question needed to resolve their uncertainty. The user reviews or edits the follow-up before explicitly sending.

After the new response arrives, VERIFY checks the combined first and follow-up responses against approved intent. Update the same requirement list, retain the earlier assessment for comparison, and show which statuses changed and the follow-up evidence resolving them. Report any remaining material gaps honestly. Preserve Needs review in VERIFY whenever the evidence remains insufficient; do not convert uncertainty into a confident status.

Acceptance criteria:
- Generating a follow-up does not send it without user action.
- A real follow-up model response is received before improvement is verified.
- Before/after counts and resolved gaps follow the actual second evaluation.
- The app never assumes success merely because it generated or sent a fix.
- The complete POST -> NEXT -> VERIFY trail is saved in the interaction.

Source: `scope.md > The Core Loop`, `What "Working" Looks Like`, and `Explicitly Cut`.

### Minimal Interaction History

An Interaction begins when the user first clicks "Review with PickyLens". Simply opening the workspace or editing the prefilled prompt before that action does not create a History entry. Once PRE begins, create and save the Interaction automatically and update its saved state after every meaningful step, not only upon completion. Preserve the original request, PRE findings, accepted clarifications, approved intent, selected prompt, AI responses, POST assessments and evidence, generated follow-up and its edits, VERIFY results, failure/recovery state, current workflow stage, mode, available model/provider metadata, and timestamps.

Closing and reopening the app must retain progress. Incomplete and failed interactions remain in History and reopen at their last meaningful state rather than restarting. Read-only detail preserves the evidence trail, with understandable statuses such as Incomplete, Failed at POST, or Recovered after retry when supported by actual events.

Terminal states include "Complete after first response", "Complete after verification", and "Completed with review items". Unresolved review items can be resumed while the interaction remains nonterminal; explicitly ending as Completed with review items makes it terminal. Terminal History remains read-only with no Resume action. "Continue as new interaction" and "Duplicate" are future features, not MVP behaviors.

Acceptance criteria:
- Opening the workspace or editing the prefilled prompt before the first "Review with PickyLens" click creates no History entry.
- The first "Review with PickyLens" click creates and saves the Interaction as PRE begins; every subsequent meaningful step updates it, and completed, incomplete, and failed work survives closing and reopening.
- Resume is available only for nonterminal work and returns to the main workspace at the last meaningful workflow state with all saved context and completed stages.
- Terminal interactions, including Completed with review items, offer no Resume and remain uneditable.
- Each list row shows an automatically generated human-readable title, date/time, mode, and current/final status.
- A selected interaction exposes its completed stages, approved intent, responses, reviews, follow-up, and final verification where present.
- Incomplete interactions retain completed evidence and the failed/stopped stage.
- History provides no search, filtering, editing, deletion, export, analytics, comparison, accounts, or multi-user features.

Source: `scope.md > Minimal Interaction History` and `The Core Loop`; learner's explicit persistence and History decisions.

### Empty Requests and Empty History

An empty or whitespace-only prompt does not run PRE. Disable actions requiring a request, show "Enter a request to begin.", and produce no findings or readiness score.

Text that is not an actionable request can still be reviewed. PRE normally returns Red with a clear explanation such as "PickyLens cannot determine what you want the AI to produce." Ask for the minimum missing information needed to establish a usable request; do not invent a task. The established Red override remains applicable.

When History has no saved entries, show "No interactions yet." and "Completed and in-progress PickyLens reviews will appear here." Offer one clear "Start an interaction" action returning to the main workspace. Never populate History with fake examples.

Acceptance criteria:
- Blank/whitespace input disables request-dependent actions and cannot trigger PRE or a readiness score.
- Nonblank unusable input can be reviewed and prompts for missing task information without fabricating intent.
- Empty History shows the specified message and a workspace action, with no fake entries.

Source: learner's explicit empty-state decisions; develops `scope.md > The Core Loop` and the minimal History addition.

## States and Boundaries

- **Initial:** prefilled editable scenario, Replay Demo selected, PRE highlighted, no findings before review.
- **Material decision needed:** ask the user; do not silently decide or change intent.
- **Replay incompatibility:** explain the issue, block the fixture, and offer canonical reset or Live Model.
- **Failure:** identify the failed stage with concise wording such as "AI response failed", "POST review could not be completed", or "Follow-up request failed". Explain the immediate consequence without unnecessary technical detail.
- **Preserved work:** retain every successfully completed request, clarification, approved intent, answer, review, and generated/edited follow-up.
- **Recovery:** allow retry of the failed step, relevant prompt editing where appropriate, return to the previous completed stage, or stop and save as incomplete. A successful retry resumes at the failed stage instead of restarting the entire flow.
- **No false success:** unfinished or failed stages are never marked successful. Verified improvement and remaining gaps follow the evidence.
- **Needs review:** count uncertainty separately, explain the evidence limitation, and preserve the status through VERIFY if it remains unresolved. User-approved questions may help resolve it without treating it as an automatic omission.

Source: `scope.md > What "Working" Looks Like` and learner's failure/recovery requirements.

## Product Decisions

- Manual initiation and prompt choice preserve human ownership of intent.
- Replay controls only the first response, making the material-defect demonstration repeatable without forcing a live model to fail.
- Conservative replay compatibility prevents misleading use of an unrelated answer.
- Evidence-backed POST and repeated verification demonstrate improvement instead of assuming it.
- Minimal History is required because traceability is part of PickyLens's value; reduce settings complexity rather than remove any core stage.
- Use a single model configured outside the UI; retain the full core cycle.
- Adopt the learner's professional, restrained visual direction without locking iconography.

## What We're Building

One web workspace, Replay Demo and Live Model, manual PRE and human clarification, prompt selection, evidence-backed POST, editable minimal follow-up and explicit send, dynamic VERIFY, minimal Interactions list/detail, and graceful failures with preserved work and retry.

Minimal History is reconciled in `scope.md > Minimal Interaction History`. The amended scope is approved; no other scope area was expanded.

## Deferred From the POC

Smart/Always modes, host integrations, Gemini hooks, provider configuration screens, multiple-model selection, and commercial settings are outside the MVP. No advanced recovery, background retries, or complex error diagnostics. Continue-as-new and Duplicate capabilities are future features; completed interactions cannot be edited or resumed. Deployment remains optional.

## Non-Goals

A polished commercial product; fabricated findings or predetermined success; intentionally forcing the live model to fail; repeating the entire task to repair a gap; additional History features or multi-user infrastructure.

Source: `scope.md > The POC Boundary`, `Later`, and `Explicitly Cut`, plus the learner's explicit exclusions.

## Open Questions

No unresolved product-behavior decisions remain from the current interview. The minimal History amendment is now recorded in scope.md; both the amended scope and this PRD are approved.

Review format: canonical Markdown plus a visual HTML companion, as requested by the learner. Technical implementation and styling details belong to 4-spec after product approval, not this interview.


## Authorized Replay Quality-Defect Amendment

Replay requires a genuine, unmanipulated response containing at least one material quality defect that PickyLens can identify and demonstrate meaningfully, such as an omission, contradiction, inconsistency, or unresolved uncertainty. Preserve the response exactly as captured and retain provenance. Never insert or manufacture a defect or hardcode an expected Replay assessment. Partial means addressed but materially inconsistent or unreliable; Needs review means evidence is insufficient to establish whether an apparent inconsistency is real.

## Authorized New-Case and Active-Case Orientation

New cases retain the full introduction, first-use guide, human-language process, and two-sided workbench headings until Review my request begins. Active cases collapse introductory decoration and retain a compact sticky header/navigation/mode control, process progress with current/completed/future states, and request/answer orientation links. Narrow screens use shorter orientation labels and hide secondary methodology abbreviations. Starting a new case automatically restores the full introduction. This is presentation derived from interaction state, with no preference, persistence, provider, or recovery change.
