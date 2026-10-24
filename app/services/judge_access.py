"""Atomic, persistent limits. Tokens are hashed; failed attempts still consume allowance."""
import contextvars
import hashlib
import hmac
import json
import secrets
import sqlite3
import time
from pathlib import Path
from app.providers.telemetry import calls

principal = contextvars.ContextVar('judge_pass', default=None)
PUBLIC_MESSAGE = 'Public demo allowance reached. Please try again later.'
MESSAGE = 'Your PickyLens evaluation allowance has been reached.'

class AccessDenied(ValueError):
    pass

class JudgeAccess:
    def __init__(self, path, global_limit=200, per_minute=6, token_limit=2000000, *, anonymous_operations=12, anonymous_hours=24, anonymous_per_minute=6, anonymous_ip_operations=30, anonymous_ip_hours=24, devpost_operations=30, devpost_hours=72, devpost_per_minute=6, devpost_ip_operations=60, devpost_ip_hours=72):
        self.anonymous_operations, self.anonymous_hours = anonymous_operations, anonymous_hours
        self.anonymous_per_minute, self.anonymous_ip_operations = anonymous_per_minute, anonymous_ip_operations
        self.anonymous_ip_hours = anonymous_ip_hours
        self.devpost_operations, self.devpost_hours = devpost_operations, devpost_hours
        self.devpost_per_minute, self.devpost_ip_operations, self.devpost_ip_hours = devpost_per_minute, devpost_ip_operations, devpost_ip_hours
        self.token_limit = token_limit
        self.path, self.global_limit, self.per_minute = str(path), global_limit, per_minute
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''CREATE TABLE IF NOT EXISTS passes (digest TEXT PRIMARY KEY, expires REAL NOT NULL, maximum INTEGER NOT NULL, used INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS reservations (id INTEGER PRIMARY KEY, digest TEXT NOT NULL, created REAL NOT NULL);''')

            pass_columns = {r[1] for r in db.execute('PRAGMA table_info(passes)')}
            if 'kind' not in pass_columns:
                db.execute("ALTER TABLE passes ADD COLUMN kind TEXT NOT NULL DEFAULT 'judge'")
                db.execute("ALTER TABLE passes ADD COLUMN ip_digest TEXT")
            if 'traffic' not in pass_columns:
                db.execute("ALTER TABLE passes ADD COLUMN traffic TEXT NOT NULL DEFAULT 'normal'")
            db.execute('CREATE TABLE IF NOT EXISTS access_settings (name TEXT PRIMARY KEY, value TEXT NOT NULL)')
            db.execute('INSERT OR IGNORE INTO access_settings VALUES (?,?)', ('ip_salt', secrets.token_hex(32)))
            self.ip_salt = db.execute("SELECT value FROM access_settings WHERE name='ip_salt'").fetchone()[0]
            columns = {r[1] for r in db.execute('PRAGMA table_info(reservations)')}
            if 'tokens' not in columns:
                db.execute('ALTER TABLE reservations ADD COLUMN tokens INTEGER NOT NULL DEFAULT 300000')
            if 'metadata' not in columns:
                db.execute("ALTER TABLE reservations ADD COLUMN metadata TEXT NOT NULL DEFAULT '[]'")

    def connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def issue(self, maximum=30, hours=72):
        if not 0 < maximum <= self.global_limit or not 0 < hours <= 720:
            raise ValueError('Invalid allowance or expiration')
        token = secrets.token_urlsafe(32)
        with self.connect() as db:
            db.execute('INSERT INTO passes(digest,expires,maximum) VALUES(?,?,?)', (self.digest(token), time.time()+hours*3600, maximum))
        return token

    @staticmethod
    def digest(token):
        return hashlib.sha256(token.encode()).hexdigest()

    def validate(self, token):
        digest = self.digest(token)
        with self.connect() as db:
            row = db.execute("SELECT expires FROM passes WHERE digest=? AND kind='judge'", (digest,)).fetchone()
        if not row or row[0] <= time.time():
            raise AccessDenied('Your Judge Pass is invalid or expired.')
        return digest

    def anonymous(self, token, address, *, devpost=False):
        ip_digest = hmac.new(self.ip_salt.encode(), address.encode(), hashlib.sha256).hexdigest()
        with self.connect() as db:
            row = db.execute("SELECT digest FROM passes WHERE digest=? AND kind='anonymous' AND expires>? AND ip_digest=?", (self.digest(token), time.time(), ip_digest)).fetchone()
            if row:
                return row[0], None
            token = secrets.token_urlsafe(32)
            digest = self.digest(token)
            hours = self.devpost_hours if devpost else self.anonymous_hours
            maximum = self.devpost_operations if devpost else self.anonymous_operations
            db.execute("INSERT INTO passes(digest,expires,maximum,kind,ip_digest,traffic) VALUES (?,?,?,'anonymous',?,?)", (digest, time.time()+hours*3600, maximum, ip_digest, 'devpost' if devpost else 'normal'))
            return digest, token

    def reserve(self):
        digest = principal.get()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT expires,maximum,used,kind,ip_digest,traffic FROM passes WHERE digest=?', (digest,)).fetchone()
            if not row or row[0] <= time.time():
                raise AccessDenied('Your Judge Pass is invalid or expired.')
            anonymous = row[3] == 'anonymous'
            message = PUBLIC_MESSAGE if anonymous else MESSAGE
            minute_limit = self.per_minute
            if anonymous:
                devpost = row[5] == 'devpost'
                minute_limit = self.devpost_per_minute if devpost else self.anonymous_per_minute
                ip_limit = self.devpost_ip_operations if devpost else self.anonymous_ip_operations
                ip_hours = self.devpost_ip_hours if devpost else self.anonymous_ip_hours
                # Count every anonymous class on this IP, not separate ref buckets.
                ip_count = db.execute('SELECT count(*) FROM reservations r JOIN passes p ON p.digest=r.digest WHERE p.ip_digest=? AND r.created>?', (row[4],time.time()-ip_hours*3600)).fetchone()[0]
                ip_recent = db.execute('SELECT count(*) FROM reservations r JOIN passes p ON p.digest=r.digest WHERE p.ip_digest=? AND r.created>?', (row[4],time.time()-60)).fetchone()[0]
                if ip_count >= ip_limit or ip_recent >= minute_limit:
                    raise AccessDenied(PUBLIC_MESSAGE)
            total = db.execute('SELECT count(*) FROM reservations').fetchone()[0]
            if row[2] >= row[1] or total >= self.global_limit:
                raise AccessDenied(message)
            charged = db.execute('SELECT coalesce(sum(tokens),0) FROM reservations').fetchone()[0]
            if charged + 300000 > self.token_limit:
                raise AccessDenied(message)
            recent = db.execute('SELECT count(*) FROM reservations WHERE digest=? AND created>?', (digest,time.time()-60)).fetchone()[0]
            if recent >= minute_limit:
                raise AccessDenied(PUBLIC_MESSAGE if anonymous else 'Please wait a minute before another PickyLens operation.')
            db.execute('UPDATE passes SET used=used+1 WHERE digest=?', (digest,))
            cursor = db.execute('INSERT INTO reservations(digest,created) VALUES(?,?)', (digest,time.time()))
            return cursor.lastrowid

    def settle(self, reservation, records):
        # Unknown usage, interrupted calls and missing telemetry retain the full reservation.
        known = records and all(r.total_tokens is not None for r in records)
        tokens = sum(r.total_tokens for r in records) if known else 300000
        metadata = json.dumps([r.model_dump(mode='json') for r in records])
        with self.connect() as db:
            db.execute('UPDATE reservations SET tokens=?,metadata=? WHERE id=?', (tokens,metadata,reservation))

class BoundedProvider:
    def __init__(self, provider, access):
        self.provider, self.access, self.test_stub = provider, access, provider.test_stub

    def reserve(self, context):
        if len(json.dumps(context)) > 60000:
            raise AccessDenied('This interaction is too long for the evaluation allowance.')
        return self.access.reserve()

    async def perform(self, context, fn, *args):
        reservation = self.reserve(context)
        outer = calls.get()
        records = []
        token = calls.set(records)
        try:
            return await fn(context, *args)
        finally:
            calls.reset(token)
            if outer is not None:
                outer.extend(records)
            self.access.settle(reservation, records)

    async def generate_structured(self, context, result_schema, purpose):
        return await self.perform(context, self.provider.generate_structured, result_schema, purpose)

    async def generate_text(self, context, purpose):
        return await self.perform(context, self.provider.generate_text, purpose)
