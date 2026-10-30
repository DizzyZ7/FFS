"""Local durable idempotency ledger for a single paid generation dispatch.

A reserved request is NEVER automatically retried: an interrupted request may
have reached the vendor. Operator reconciliation is required.
"""
import json
import os
import re
import uuid
from pathlib import Path

_KEY=re.compile(r'^[a-zA-Z0-9_-]{8,128}$')

def _ledger_dir(folder:Path):
    path=folder/'generation-dispatch'
    path.mkdir(exist_ok=True)
    return path

def _read_reservation(path:Path):
    """Corrupted ledger must never be interpreted as a missing reservation."""
    try:
        payload=json.loads(path.read_text(encoding='utf8'))
    except (UnicodeError, OSError, json.JSONDecodeError) as exc:
        raise ValueError('Dispatch reservation is unreadable; manual reconciliation required') from exc
    if (not isinstance(payload,dict)
            or not isinstance(payload.get('idempotency_key'),str)
            or not isinstance(payload.get('shot_id'),str)
            or not isinstance(payload.get('fingerprint'),str)
            or not re.fullmatch(r'[0-9a-f]{64}',payload['fingerprint'])
            or not payload['shot_id']
            or payload.get('state')!='reserved'):
        raise ValueError('Dispatch reservation is invalid; manual reconciliation required')
    if payload['idempotency_key']!=path.stem:
        raise ValueError('Dispatch reservation key mismatch; manual reconciliation required')
    return payload

def bind_dispatch_job(folder:Path,key:str,job_id:str):
    """Bind an existing reservation to one immutable queue job ID."""
    if not isinstance(job_id,str) or not re.fullmatch(r'[0-9a-f]{32}',job_id):
        raise ValueError('Invalid job ID')
    reservation=get_dispatch(folder,key)
    path=folder/'generation-dispatch'/(key+'.job')
    try:
        with path.open('x',encoding='utf8') as output:
            output.write(job_id)
            output.flush()
            os.fsync(output.fileno())
        return job_id
    except FileExistsError:
        existing=path.read_text(encoding='utf8')
        if existing!=job_id:
            raise ValueError('Dispatch reservation is bound to another job')
        return existing

def get_dispatch_job(folder:Path,key:str):
    get_dispatch(folder,key)
    path=folder/'generation-dispatch'/(key+'.job')
    if not path.exists():
        return None
    job_id=path.read_text(encoding='utf8')
    if not re.fullmatch(r'[0-9a-f]{32}',job_id):
        raise ValueError('Dispatch job binding is invalid; manual reconciliation required')
    return job_id

def reserve_dispatch(folder:Path,key:str,shot_id:str,fingerprint:str):
    if not isinstance(key,str) or not _KEY.fullmatch(key):
        raise ValueError('Invalid idempotency key')
    if not isinstance(shot_id,str) or not shot_id:
        raise ValueError('Invalid shot ID')
    if not isinstance(fingerprint,str) or not re.fullmatch(r'[0-9a-f]{64}',fingerprint):
        raise ValueError('Invalid fingerprint')
    path=_ledger_dir(folder)/(key+'.json')
    payload={'idempotency_key':key,'shot_id':shot_id,
             'fingerprint':fingerprint,'state':'reserved'}
    try:
        with path.open('x',encoding='utf8') as output:
            json.dump(payload,output)
            output.flush()
            os.fsync(output.fileno())
        return {'created':True,**payload}
    except FileExistsError:
        existing=_read_reservation(path)
        if existing['shot_id']!=shot_id or existing['fingerprint']!=fingerprint:
            raise ValueError('Idempotency key reused for a different shot or revision')
        return {'created':False,**existing}

def get_dispatch(folder:Path,key:str):
    if not isinstance(key,str) or not _KEY.fullmatch(key):
        raise ValueError('Invalid idempotency key')
    path=folder/'generation-dispatch'/(key+'.json')
    if not path.is_file():
        raise FileNotFoundError(key)
    return _read_reservation(path)
