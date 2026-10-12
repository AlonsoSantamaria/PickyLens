"""Read-only engineering summary. No dashboard or public score."""
import argparse
import json
from app.storage.repository import Repository

def summarize(s):
    post = s.post.counts() if s.post else None
    return {"interaction_id": s.interaction_id, "status": s.lifecycle_status,
        "pre_readiness": s.pre.readiness if s.pre else None,
        "post_counts": post,
        "material_issue_detected": bool(post["partial"] or post["missing"]) if post else None,
        "next_required": bool(post["partial"] or post["missing"] or s.approved_uncertainty) if post else None,
        "next_generated": s.next is not None,
        "verify_counts": s.verification.counts() if s.verification else None,
        "model_call_count": len(s.model_calls),
        "usage": {key: sum(getattr(c,key) or 0 for c in s.model_calls) for key in ("input_tokens","output_tokens","reasoning_tokens","total_tokens","duration_ms")},
        "usage_available_calls": sum(c.total_tokens is not None for c in s.model_calls),
        "calls": [c.model_dump(mode="json") for c in s.model_calls]}

if __name__ == "__main__":
    parser=argparse.ArgumentParser();parser.add_argument("database");parser.add_argument("interaction_id")
    args=parser.parse_args()
    print(json.dumps(summarize(Repository(args.database).get(args.interaction_id)),indent=2))
