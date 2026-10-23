"""Atomic, persistent limits. Tokens are hashed; failed attempts still consume allowance."""
import contextvars
import hashlib
import json
import secrets
import sqlite3
import time
from pathlib import Path

principal = contextvars.ContextVar('judge_pass', default=None)
MESSAGE = 'Your PickyLens evaluation allowance has been reached.'

class AccessDenied(ValueError):
    pass

class JudgeAccess:
    def __init__(self, path, global_limit=200, per_minute=6):
        self.path, self.global_limit, self.per_minute = str(path), global_limit, per_minute
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''CREATE TABLE IF NOT EXISTS passes (digest TEXT PRIMARY KEY, expires REAL NOT NULL, maximum INTEGER NOT NULL, used INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS reservations (id INTEGER PRIMARY KEY, digest TEXT NOT NULL, created REAL NOT NULL);''')

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
            row = db.execute('SELECT expires FROM passes WHERE digest=?', (digest,)).fetchone()
        if not row or row[0] <= time.time():
            raise AccessDenied('Your Judge Pass is invalid or expired.')
        return digest

    def reserve(self):
        digest = principal.get()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT expires,maximum,used FROM passes WHERE digest=?', (digest,)).fetchone()
            if not row or row[0] <= time.time():
                raise AccessDenied('Your Judge Pass is invalid or expired.')
            total = db.execute('SELECT count(*) FROM reservations').fetchone()[0]
            if row[2] >= row[1] or total >= self.global_limit:
                raise AccessDenied(MESSAGE)
            recent = db.execute('SELECT count(*) FROM reservations WHERE digest=? AND created>?', (digest,time.time()-60)).fetchone()[0]
            if recent >= self.per_minute:
                raise AccessDenied('Please wait a minute before another PickyLens operation.')
            db.execute('UPDATE passes SET used=used+1 WHERE digest=?', (digest,))
            db.execute('INSERT INTO reservations(digest,created) VALUES(?,?)', (digest,time.time()))

class BoundedProvider:
    def __init__(self, provider, access):
        self.provider, self.access, self.test_stub = provider, access, provider.test_stub

    def reserve(self, context):
        if len(json.dumps(context)) > 60000:
            raise AccessDenied('This interaction is too long for the evaluation allowance.')
        self.access.reserve()

    async def generate_structured(self, context, result_schema, purpose):
        self.reserve(context)
        return await self.provider.generate_structured(context, result_schema, purpose)

    async def generate_text(self, context, purpose):
        self.reserve(context)
        return await self.provider.generate_text(context, purpose)
