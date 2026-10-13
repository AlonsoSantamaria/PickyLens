"""Small human-language reports; no terminal control sequences from model text."""
import re


def clean(text, limit=400):
    text = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", str(text))
    return text[:limit]


def render(s):
    lines = ["PickyLens | " + ("Check answer" if s.answer else "Review request")]
    if s.failure:
        lines.append(s.failure)
    elif s.post:
        counts = s.post.counts()
        lines.append(" | ".join(f"{counts[key]} {label}" for key, label in [
            ("complete", "Complete"), ("partial", "Partial"), ("missing", "Missing"),
            ("needs_review", "Needs review")]))
        if all(a.status == "complete" for a in s.post.assessments):
            lines.append("The answer meets the reviewed requirements. No follow-up needed.")
        else:
            for item in s.post.assessments:
                if item.status == "complete":
                    continue
                lines.append(f"{item.status.value.replace('_', ' ').title()}: {clean(item.requirement_text)}")
                lines.append(clean(item.uncertainty_reason or item.explanation))
                for evidence in item.evidence[:2]:
                    lines.append("Evidence: " + clean(evidence.excerpt, 220))
            if counts["partial"] or counts["missing"]:
                lines.append("Next: request a targeted repair draft if useful; nothing is sent automatically.")
            if counts["needs_review"]:
                lines.append("Uncertainty remains. Inspect it or leave unresolved; it is not treated as missing.")
    elif s.pre:
        lines.append({"green": "Ready to send.", "amber": "Usable, but worth improving.",
                      "red": "Important issue before sending."}[s.pre.readiness])
        for finding in s.pre.findings[:3]:
            lines.append(clean(finding.title) + ": " + clean(finding.explanation))
        if s.pre.clarifications:
            lines.append("Suggested clarifications are not accepted automatically.")
        lines.append("Advisory only. Gemini continues with your unchanged request.")
    else:
        lines.append("Review is incomplete; no successful assessment is available.")
    if s.next:
        lines += ["Repair draft (not sent):", clean(s.next.text, 4000)]
    lines.append("Record: " + s.interaction_id)
    return "\n".join(lines)
