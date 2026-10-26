import sqlite3
import logging
from pathlib import Path
from app.core.contracts import Snapshot, EventPayload, uid, now, FailureDiagnostic


class Conflict(ValueError):
    pass


class Repository:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript(Path(__file__).with_name("schema.sql").read_text())

    def connect(self):
        db = sqlite3.connect(self.path)
        db.execute("PRAGMA foreign_keys=ON")
        db.row_factory = sqlite3.Row
        return db

    def get(self, id):
        with self.connect() as db:
            row = db.execute("SELECT snapshot_json FROM interactions WHERE interaction_id=?", (id,)).fetchone()
        if not row:
            raise KeyError(id)
        return Snapshot.model_validate_json(row[0])

    def list(self):
        with self.connect() as db:
            return [Snapshot.model_validate_json(r[0]) for r in db.execute("SELECT snapshot_json FROM interactions ORDER BY updated_at DESC")]

    def trace(self, id):
        with self.connect() as db:
            rows = db.execute("SELECT event_type, timestamp, payload_json FROM interaction_events WHERE interaction_id=? ORDER BY sequence_number", (id,)).fetchall()
        return [{"type": r[0], "timestamp": r[1], "snapshot": EventPayload.model_validate_json(r[2]).snapshot, "superseded": EventPayload.model_validate_json(r[2]).superseded_snapshot} for r in rows]

    def save(self, snapshot, event_type, operation_id, expected_revision=None, claim=False, signature=None, superseded=None):
        snapshot = Snapshot.model_validate(snapshot.model_dump(warnings=False))
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            previous = db.execute("SELECT revision FROM interactions WHERE interaction_id=?", (snapshot.interaction_id,)).fetchone()
            if previous and previous[0] != expected_revision:
                raise Conflict("The saved interaction changed. Reload before continuing.")
            snapshot.revision = (previous[0] if previous else 0) + 1
            snapshot.last_event_sequence += 1
            snapshot.updated_at = now()
            payload = EventPayload(snapshot=snapshot, operation_id=operation_id, request_signature=signature, superseded_snapshot=superseded).model_dump_json()
            db.execute("INSERT INTO interactions VALUES (?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(interaction_id) DO UPDATE SET schema_version=excluded.schema_version,title=excluded.title,mode=excluded.mode,stage=excluded.stage,lifecycle_status=excluded.lifecycle_status,current_intent_version=excluded.current_intent_version,revision=excluded.revision,last_event_sequence=excluded.last_event_sequence,updated_at=excluded.updated_at,snapshot_json=excluded.snapshot_json", (
                snapshot.interaction_id, snapshot.schema_version, snapshot.title, snapshot.mode, snapshot.stage,
                snapshot.lifecycle_status, snapshot.intent.version if snapshot.intent else None, snapshot.revision,
                snapshot.last_event_sequence, snapshot.created_at, snapshot.updated_at, snapshot.model_dump_json()))
            db.execute("INSERT INTO interaction_events VALUES (?,?,?,?,?,?,?,?,?)", (
                uid(), snapshot.interaction_id, event_type, snapshot.last_event_sequence, snapshot.updated_at,
                operation_id if claim else None, snapshot.intent.version if snapshot.intent else None, 1, payload))
        return snapshot

    def duplicate(self, operation_id, signature, interaction_id=None):
        with self.connect() as db:
            row = db.execute("SELECT interaction_id,payload_json FROM interaction_events WHERE operation_id=?", (operation_id,)).fetchone()
            if not row:
                return None
            payload = EventPayload.model_validate_json(row[1])
            if payload.request_signature != signature or (interaction_id and row[0] != interaction_id):
                raise Conflict("Operation ID was already used for a different action.")
            current = self.get(row[0])
            if current.pending_operation == operation_id:
                return current
            rows = db.execute("SELECT payload_json FROM interaction_events WHERE interaction_id=? ORDER BY sequence_number DESC", (row[0],)).fetchall()
            for result in rows:
                event = EventPayload.model_validate_json(result[0])
                if event.operation_id == operation_id:
                    return event.snapshot
            return payload.snapshot

    def finish(self, result, operation_id, event_type):
        for attempt in range(5):
            try:
                return self._finish(result, operation_id, event_type)
            except Conflict:
                if attempt == 4:
                    raise
            except sqlite3.DatabaseError:
                diagnostic = FailureDiagnostic(failure_layer="persistence", stage=result.pending_action or result.stage,
                    validation_code="snapshot_event_transaction_failed",
                    response_id=result.model_calls[-1].response_id if result.model_calls else None,
                    call_id=result.model_calls[-1].call_id if result.model_calls else None)
                # If SQLite is unavailable, the service journal is the durable diagnostic
                # sink. The prior pending snapshot survives for explicit recovery.
                logging.getLogger(__name__).error("PickyLens persistence failure: %s", diagnostic.model_dump_json())
                raise

    def _finish(self, result, operation_id, event_type):
        # The operation token survives trace-only revision changes, but not supersession.
        current = self.get(result.interaction_id)
        known = {c.call_id for c in current.model_calls}
        merged = current.model_calls + [c for c in result.model_calls if c.call_id not in known]
        if current.pending_operation != operation_id:
            current.model_calls = merged
            return self.save(current, "superseded_result", operation_id, current.revision, superseded=result)
        result.model_calls = merged
        result.revision = current.revision
        result.last_event_sequence = current.last_event_sequence
        result.pending_operation = result.pending_action = None
        return self.save(result, event_type, operation_id, current.revision)

    def recover_interrupted(self):
        for snapshot in self.list():
            if snapshot.pending_operation:
                op = snapshot.pending_operation
                snapshot.failed_action = snapshot.pending_action
                snapshot.failure = "Operation interrupted. Completed work is saved; retry explicitly."
                snapshot.lifecycle_status = "Interrupted"
                snapshot.pending_operation = snapshot.pending_action = None
                self.save(snapshot, "operation_interrupted", op, snapshot.revision)
