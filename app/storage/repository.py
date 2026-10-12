import sqlite3
from pathlib import Path
from app.core.contracts import Snapshot, EventPayload, uid, now


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
        return [{"type": r[0], "timestamp": r[1], "snapshot": EventPayload.model_validate_json(r[2]).snapshot} for r in rows]

    def save(self, snapshot, event_type, operation_id, expected_revision=None, claim=False):
        snapshot = Snapshot.model_validate(snapshot.model_dump(warnings=False))
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            previous = db.execute("SELECT revision FROM interactions WHERE interaction_id=?", (snapshot.interaction_id,)).fetchone()
            if previous and previous[0] != expected_revision:
                raise Conflict("The saved interaction changed. Reload before continuing.")
            snapshot.revision = (previous[0] if previous else 0) + 1
            snapshot.last_event_sequence += 1
            snapshot.updated_at = now()
            payload = EventPayload(snapshot=snapshot, operation_id=operation_id).model_dump_json()
            db.execute("INSERT INTO interactions VALUES (?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(interaction_id) DO UPDATE SET schema_version=excluded.schema_version,title=excluded.title,mode=excluded.mode,stage=excluded.stage,lifecycle_status=excluded.lifecycle_status,current_intent_version=excluded.current_intent_version,revision=excluded.revision,last_event_sequence=excluded.last_event_sequence,updated_at=excluded.updated_at,snapshot_json=excluded.snapshot_json", (
                snapshot.interaction_id, snapshot.schema_version, snapshot.title, snapshot.mode, snapshot.stage,
                snapshot.lifecycle_status, snapshot.intent.version if snapshot.intent else None, snapshot.revision,
                snapshot.last_event_sequence, snapshot.created_at, snapshot.updated_at, snapshot.model_dump_json()))
            db.execute("INSERT INTO interaction_events VALUES (?,?,?,?,?,?,?,?,?)", (
                uid(), snapshot.interaction_id, event_type, snapshot.last_event_sequence, snapshot.updated_at,
                operation_id if claim else None, snapshot.intent.version if snapshot.intent else None, 1, payload))
        return snapshot
