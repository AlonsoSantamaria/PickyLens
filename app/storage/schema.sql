PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS interactions (
 interaction_id TEXT PRIMARY KEY, schema_version INTEGER NOT NULL, title TEXT NOT NULL,
 mode TEXT NOT NULL, stage TEXT NOT NULL, lifecycle_status TEXT NOT NULL,
 current_intent_version INTEGER, revision INTEGER NOT NULL, last_event_sequence INTEGER NOT NULL,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL, snapshot_json TEXT NOT NULL CHECK(json_valid(snapshot_json))
);
CREATE TABLE IF NOT EXISTS interaction_events (
 event_id TEXT PRIMARY KEY, interaction_id TEXT NOT NULL REFERENCES interactions(interaction_id),
 event_type TEXT NOT NULL, sequence_number INTEGER NOT NULL, timestamp TEXT NOT NULL,
 operation_id TEXT, approved_intent_version INTEGER, payload_schema_version INTEGER NOT NULL,
 payload_json TEXT NOT NULL CHECK(json_valid(payload_json)), UNIQUE(interaction_id, sequence_number)
);
CREATE UNIQUE INDEX IF NOT EXISTS operation_identity ON interaction_events(operation_id) WHERE operation_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS interaction_order ON interactions(updated_at);
CREATE TRIGGER IF NOT EXISTS immutable_events_update BEFORE UPDATE ON interaction_events BEGIN SELECT RAISE(ABORT, 'Events are append-only'); END;
CREATE TRIGGER IF NOT EXISTS immutable_events_delete BEFORE DELETE ON interaction_events BEGIN SELECT RAISE(ABORT, 'Events are append-only'); END;
