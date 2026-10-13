---
doc: product-observations
status: deferred
---

# Deferred optimization observations

Recorded 2026-10-12 following user approval of Live Web milestone `aeb5c6a`. That milestone and the completed 5-build records remain closed.

1. PRE should surface only clarifications likely to materially improve the result. Six optional clarifications can create excessive friction. Evaluate clarification relevance and presentation later; do not change the current evaluator during Gemini adapter work.
2. The measured complete-without-repair path used 9,196 tokens and approximately 58 seconds of model-call time for PRE, the answer, and POST. This is an observation from one run, not a performance benchmark or commercial cost forecast. Later investigate deterministic/cheap-first evaluation, cheaper model routing, justified escalation, and host-native inference where available.

Neither optimization is authorized for implementation in the next milestone. Investigating host capabilities for the Gemini architecture does not authorize provider replacement or optimization work.

3. Approved Gemini v0.1 qualification (2026-10-13): investigate a more natural/native manual invocation in a later UX task. Shell passthrough remains a technical fallback, not final judge-facing or commercial UX. Do not build a separate command system now.

The user approved this deferred backlog as the Gemini planning baseline on 2026-10-13.
