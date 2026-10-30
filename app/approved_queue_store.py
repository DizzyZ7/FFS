"""Atomic local approval reservation and queue journal.

SQLite transaction is the source of truth for newly approved local jobs.
It does not call any paid provider or claim distributed exactly-once execution.
"""
import json
import sqlite3
import uuid
import re
from pathlib import Path

def reserve_approved_job(folder:Path,key:str,shot_id:str,fingerprint:str):
    from .generation_dispatch import _KEY
    if not isinstance(key,str) or not _KEY.fullmatch(key):
        raise ValueError('Invalid idempotency key')
    if not isinstance(shot_id,str) or not shot_id:
        raise ValueError('Invalid shot ID')
    if not isinstance(fingerprint,str) or not re.fullmatch(r'[0-9a-f]{64}',fingerprint):
        raise ValueError('Invalid fingerprint')
    folder=Path(folder)
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
                try:
                    job=json.loads(row[3])
                except (TypeError, ValueError) as exc:
                    raise ValueError('Corrupt approved job journal; manual reconciliation required') from exc
                if (not isinstance(job,dict)
                        or job.get('id')!=row[2]
                        or job.get('shot_id')!=shot_id
                        or job.get('fingerprint')!=fingerprint
                        or job.get('status') not in ('queued','running','succeeded','failed','cancelled')):
                    raise ValueError('Approved job identity mismatch; manual reconciliation required')
                result={'created':False,'job':job}
            else:
                # Legacy JSON ledger is still active in the API. Never mint a
                # second job for a key already reserved by that ledger.
                legacy=folder/'generation-dispatch'/(key+'.json')
                if legacy.exists() or legacy.is_symlink():
                    raise ValueError('Legacy dispatch reservation exists; manual reconciliation required')
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
