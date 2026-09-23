import hashlib
import hmac
import json
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_DB = "data/capture.sqlite"


def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def db_path():
    return Path(os.environ.get("DB_PATH", DEFAULT_DB))


def connect(path=None):
    path = Path(path or db_path())
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("pragma journal_mode=wal")
    init(conn)
    return conn


def init(conn):
    conn.executescript(
        """
        create table if not exists api_keys (
            id integer primary key autoincrement,
            name text not null unique,
            prefix text not null,
            key_hash text not null,
            created_at text not null
        );
        create table if not exists captures (
            id integer primary key autoincrement,
            api_key_id integer,
            api_key_name text,
            provider text not null,
            endpoint text not null,
            method text not null,
            path text not null,
            request_headers text not null,
            request_body text not null,
            response_body text not null,
            strategy text not null,
            created_at text not null,
            foreign key(api_key_id) references api_keys(id)
        );
        """
    )
    conn.commit()


def hash_key(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def make_key(name):
    raw = secrets.token_urlsafe(32)
    return f"wws_{name}_{raw}"


def create_api_key(name):
    token = make_key(name)
    prefix = token[:14]
    with connect() as conn:
        conn.execute(
            "insert into api_keys (name, prefix, key_hash, created_at) values (?, ?, ?, ?)",
            (name, prefix, hash_key(token), now_iso()),
        )
        conn.commit()
    return token


def list_api_keys():
    with connect() as conn:
        return [dict(row) for row in conn.execute("select id, name, prefix, created_at from api_keys order by name")]


def rename_api_key(original, new):
    with connect() as conn:
        cur = conn.execute("update api_keys set name = ? where name = ?", (new, original))
        conn.execute("update captures set api_key_name = ? where api_key_name = ?", (new, original))
        conn.commit()
        return cur.rowcount


def delete_api_key(name):
    with connect() as conn:
        cur = conn.execute("delete from api_keys where name = ?", (name,))
        conn.commit()
        return cur.rowcount


def find_api_key(token):
    if not token:
        return None
    digest = hash_key(token)
    with connect() as conn:
        row = conn.execute("select id, name, prefix from api_keys where key_hash = ?", (digest,)).fetchone()
    return dict(row) if row else None


def verify_api_key(token):
    return find_api_key(token) is not None


def capture(api_key, provider, endpoint, method, path, headers, body, response, strategy):
    created_at = now_iso()
    with connect() as conn:
        conn.execute(
            """
            insert into captures (
                api_key_id, api_key_name, provider, endpoint, method, path,
                request_headers, request_body, response_body, strategy, created_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                api_key["id"] if api_key else None,
                api_key["name"] if api_key else "unknown",
                provider,
                endpoint,
                method,
                path,
                json.dumps(headers, ensure_ascii=False),
                body,
                json.dumps(response, ensure_ascii=False),
                strategy,
                created_at,
            ),
        )
        conn.commit()
    return created_at


def history(limit=50, key=None, provider=None, contains=None, since=None):
    where = []
    args = []
    if key:
        where.append("api_key_name = ?")
        args.append(key)
    if provider:
        where.append("provider = ?")
        args.append(provider)
    if contains:
        where.append("request_body like ?")
        args.append(f"%{contains}%")
    if since:
        where.append("created_at >= ?")
        args.append(since)
    clause = " where " + " and ".join(where) if where else ""
    sql = f"select * from captures{clause} order by id desc limit ?"
    args.append(limit)
    with connect() as conn:
        return [dict(row) for row in conn.execute(sql, args)]


def export_rows(limit=200):
    with connect() as conn:
        return [dict(row) for row in conn.execute("select * from captures order by id desc limit ?", (limit,))]


def safe_equals(a, b):
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))
