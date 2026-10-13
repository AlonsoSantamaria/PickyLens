"""Durable hook reservations; never guess when a session has overlapping turns."""
import hashlib
import json
from app.core.contracts import uid


class SessionStore:
    def __init__(self, repository):
        self.repo = repository
        with self.repo.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS gemini_turns (
                    id TEXT PRIMARY KEY, session_key TEXT NOT NULL, prompt TEXT NOT NULL,
                    started REAL NOT NULL, state TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS gemini_receipts (
                    key TEXT PRIMARY KEY, payload TEXT NOT NULL, interaction_id TEXT,
                    result TEXT, state TEXT NOT NULL);
            """)

    def reserve(self, hook):
        payload = hook.model_dump(mode="json")
        encoded = json.dumps(payload, sort_keys=True)
        key = hashlib.sha256(encoded.encode()).hexdigest()
        session = hashlib.sha256(json.dumps([hook.session_id, hook.cwd,
                                             hook.transcript_path]).encode()).hexdigest()
        with self.repo.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            prior = db.execute("SELECT * FROM gemini_receipts WHERE key=?", (key,)).fetchone()
            if prior:
                return key, prior["interaction_id"], prior["result"] or "Review already claimed; inspect the saved record."
            current = db.execute("SELECT * FROM gemini_turns WHERE session_key=? ORDER BY started DESC LIMIT 1",
                                 (session,)).fetchone()
            problem, interaction = None, None
            if hook.stop_hook_active:
                problem = "PickyLens did not re-review an automatic host retry. Review manually if needed."
            elif hook.hook_event_name == "BeforeAgent":
                interaction = uid()
                state = "open"
                if current and (current["state"] != "closed" or hook.timestamp.timestamp() <= current["started"]):
                    state = "ambiguous"
                    problem = "PickyLens review unavailable: overlapping or out-of-order turns. Use manual review with explicit input."
                db.execute("INSERT INTO gemini_turns VALUES (?,?,?,?,?)", (
                    interaction, session, hook.prompt, hook.timestamp.timestamp(), state))
            elif (not current or current["state"] != "open" or current["prompt"] != hook.prompt
                  or hook.timestamp.timestamp() < current["started"]):
                problem = "PickyLens answer review unavailable: no unambiguous matching request. Use manual review with explicit input."
            else:
                interaction = current["id"]
                db.execute("UPDATE gemini_turns SET state='closed' WHERE id=?", (interaction,))
            db.execute("INSERT INTO gemini_receipts VALUES (?,?,?,?,?)", (
                key, encoded, interaction, problem, "unavailable" if problem else "pending"))
        return key, interaction, problem

    def complete(self, key, message):
        with self.repo.connect() as db:
            db.execute("UPDATE gemini_receipts SET result=?, state='finished' WHERE key=?", (message, key))
