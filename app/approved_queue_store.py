"""Atomic local approval reservation and queue journal.

SQLite transaction is the source of truth for newly approved local jobs.
It does not call any paid provider or claim distributed exactly-once execution.
"""
import json
import sqlite3
import uuid
from pathlib import Path

def reserve_approved_job(folder:Path,key:str,shot_id:str,fingerprint:str):
    from .generation_dispatch import _KEY
    import re
    if not isinstance(key,str) or not _KEY.fullmatch(key):
        raise ValueError('Invalid idempotency key')
    if not isinstance(shot_id,str) or not shot_id:
        raise ValueError('Invalid shot ID')
    if not isinstance(fingerprint,str) or not re.fullmatch(r'[0-9a-f]{64}',fingerprint):
        raise ValueError('Invalid fingerprint')
    folder.mkdir(parents=True,exist_ok=True)
    path=folder/'approved-queue.sqlite3'
    with sqlite3.connect(path,timeout=15,isolation_level=None) as conn:
        conn.execute('PRAGMA busy_timeout=15000')
        conn.execute('PRAGMA synchronous=FULL')
        conn.execute('BEGIN IMMEDIATE')
        try:
            conn.execute("""CREATE TABLE IF NOT EXISTS approved_jobs (
                idempotency_key TEXT PRIMARY KEY,
                shot_id TEXT NOT NULL,
                fingerprint TEXT NOT NULL,
                job_id TEXT NOT NULL UNIQUE,
                job_json TEXT NOT NULL
            )""")
            row=conn.execute('SELECT shot_id,fingerprint,job_id,job_json FROM approved_jobs WHERE idempotency_key=?',(key,)).fetchone()
            if row is not None:
                if row[0]!=shot_id or row[1]!=fingerprint:
                    raise ValueError('Idempotency key reused for a different shot or revision')
                result={'created':False,'job':json.loads(row[3])}
            else:
                from datetime import datetime,timezone
                now=datetime.now(timezone.utc).isoformat()
                job={'id':uuid.uuid4().hex,'shot_id':shot_id,'status':'queued',
                     'created_at':now,'updated_at':now,'progress':0,
                     'output_path':None,'error':None,'fingerprint':fingerprint}
                conn.execute('INSERT INTO approved_jobs VALUES (?,?,?,?,?)',
                             (key,shot_id,fingerprint,job['id'],json.dumps(job)))
                result={'created':True,'job':job}
            conn.execute('COMMIT')
            return result
        except BaseException:
            conn.execute('ROLLBACK')
            raise
