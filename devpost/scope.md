---
doc: scope
status: approved
---

# PickyLens

An AI interaction quality layer that reviews both the request and the answer, then helps repair only what is missing.

## The Unique Kernel

"PickyLens quality-checks the whole AI interaction, not just the prompt."

PRE -> AI -> POST -> NEXT closes the loop: identify material request issues, check actual fulfillment, generate a minimal follow-up, and verify whether the combined answers resolve the gaps. A polished answer is not proof of completeness, and a proposed fix is not proof of improvement.

## Who It's For

The proof of concept follows a management consultant advising a small-business owner. The consultant asks AI for a client-ready executive recommendation memo comparing two operational alternatives using information provided in the prompt.

The memo must cover the comparison, cost, implementation time, operational risk, a reasoned recommendation, assumptions or unresolved uncertainties, questions to answer before acting, and a short executive summary.

The learner encounters ambiguous or incomplete requests and polished answers that miss requirements in their own AI work. The broader intended audience uses AI for meaningful work: consultants, analysts, researchers, students, developers, managers, and business users. Their current review practices have not been established; the demo focuses on the consultant.

## The Core Loop

The evaluation target for both POST reviews is the user's approved intent: the requirements from the original request plus any material clarification, constraint, or decision explicitly accepted by the user during PRE. PRE must not silently change the user's intent. Once the user approves a clarification or improved prompt, its explicitly accepted material clarifications, constraints, and decisions become part of what POST must verify.

Open the web app with a realistic, intentionally imperfect consultant prompt. The user deliberately initiates the PRE review through a manual action. PRE identifies material issues; the user then chooses whether to send the original prompt or the improved version. This manual control is part of the MVP. Obtain the memo, run POST against the user's approved intent, and inspect complete, partial, or missing assessments.

Use "Fix only what's missing" to generate a minimal follow-up, send it to the model, and receive a second response. Run POST again on the original answer plus the follow-up response against the user's approved intent. Show which gaps were resolved and which remain; mark improvement only when the second verification supports it.

## Inspiration & Identity

A quiet reviewer beside the AI interaction: available when needed, unobtrusive when not needed, and focused on outcomes rather than prompt-engineering theory. The user remains in control of whether to send the original request, edit it, or use an improved version. No external design reference was supplied.

## Why This Matters to the Learner

The learner repeatedly encounters quality problems on both sides of AI exchanges. They want a working PickyLens proof of concept and a disciplined development process reusable in future Neovantia products, improving delegation through clear specifications and acceptance criteria while retaining ownership of architecture and product decisions.

They also want to understand model- and host-independent core logic with optional host-specific capabilities; technical design choices belong in the later planning steps.

## What "Working" Looks Like

A judge can follow one complete consultant scenario on screen without specialized domain knowledge or prompt-engineering expertise. PRE finds consequential issues, POST exposes a genuine material quality defect in an otherwise polished memo, NEXT requests only the missing work, and a second POST demonstrates verified improvement or honestly reports remaining gaps.

The before/after requirement counts and resolved gaps reflect the actual evaluations, not predetermined success values.

A clearly labeled Replay Mode controls only the captured first AI response: a previously captured real model response with a genuine material quality defect. PRE evaluation, POST evaluation, minimal follow-up generation, the follow-up AI call, and final verification must all execute dynamically. The follow-up AI call receives a new model response; neither that response nor the evaluations are replayed or hard-coded. Document the first-response fixture transparently as a captured real model interaction.

A live mode sends the selected request to a real AI model. It does not require the first answer to contain an omission; the repeatable material-defect demonstration uses replay mode.

The target is a small proof of concept for the hackathon's short demo video and public GitHub repository, with 2-4 hours of active work as the curriculum target. Deployment is optional.

## The POC Boundary

- One simple web application and one controlled management-consultant scenario.
- The complete PRE -> AI -> POST -> NEXT flow, including a real follow-up response and re-verification of the combined result.
- Manual user control: the user deliberately initiates PRE review and chooses whether to send the original prompt or the improved version. Reviews focus on material issues.
- Replay Mode controls only the transparently documented captured first AI response. PRE evaluation, POST evaluation, minimal follow-up generation, the follow-up AI call, and final verification execute dynamically. A separate live-model path generates the first response live.
- Visible requirement fulfillment and before/after gap resolution.
- Minimal Interaction History, as bounded below: automatic persistence after the first PRE action, a simple list, read-only detail, and Resume only for nonterminal work.

Smart/Always modes, host integrations, Gemini hooks, and other commercial or future capabilities are outside the MVP. The MVP is complete through its web flow alone.

## Minimal Interaction History

An Interaction begins when the user first clicks "Review with PickyLens". Opening the workspace or editing the prefilled prompt before that action does not create a History entry. Once PRE begins, save automatically and update after every meaningful step, preserving the interaction's completed work, evidence, current state, and failure/recovery information across closing and reopening.

Provide one simple Interactions list and read-only detail. "Resume interaction" is available only for nonterminal work and returns it to the workspace at the last meaningful state. Terminal interactions remain read-only and cannot be resumed for continued work.

History has no search, filters, editing, deletion, export, analytics, comparison, accounts, or multi-user features. This amendment adds only the minimal traceability explicitly requested during the PRD interview; it does not expand any other part of the proof of concept.

## Later

A host integration, such as Gemini CLI lifecycle hooks, may be a stretch demonstration if time allows. Automatic review in environments with suitable lifecycle hooks is outside the hackathon minimum. The web proof of concept must succeed without that integration.

## Explicitly Cut

- Forcing a live model to fail or relying on probabilistic omissions for the judging demo: replay provides a repeatable, transparent demonstration.
- Predetermined evaluation results or assuming a follow-up succeeded: dynamic checks must establish the outcome.
- Repeating the entire task to repair an omission: the core value is the smallest useful follow-up.
- A polished commercial product: the learner's target is a small, convincing proof of concept.


## Authorized Replay Quality-Defect Amendment

Replay requires a genuine, unmanipulated response containing at least one material quality defect that PickyLens can identify and demonstrate meaningfully, such as an omission, contradiction, inconsistency, or unresolved uncertainty. Preserve the response exactly as captured and retain provenance. Never insert or manufacture a defect or hardcode an expected Replay assessment. Partial means addressed but materially inconsistent or unreliable; Needs review means evidence is insufficient to establish whether an apparent inconsistency is real.
