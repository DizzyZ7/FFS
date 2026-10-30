"""Deterministic revision fingerprints and safe job completion sync for recreation."""
import hashlib
import json
from pathlib import Path

def shot_fingerprint(shot):
    payload={key:shot.get(key) for key in ('id','duration','subject_ids','instructions','revision')}
    encoded=json.dumps(payload,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
    return hashlib.sha256(encoded).hexdigest()

def pending_recreation_shots(blueprint):
    return [shot for shot in blueprint['shots'] if shot.get('generation_status')!='succeeded'
            or not shot.get('output_path')]

def mark_shot_generated(blueprint,shot_id,*,fingerprint,output_path):
    import copy
    revised=copy.deepcopy(blueprint)
    shot=next((s for s in revised['shots'] if s['id']==shot_id),None)
    if shot is None:
        raise ValueError('Shot not found')
    if shot_fingerprint(shot)!=fingerprint:
        raise ValueError('Shot changed after generation began')
    if not isinstance(output_path,str) or not output_path.startswith('generated/'):
        raise ValueError('Invalid generated output path')
    shot['generation_status']='succeeded'
    shot['output_path']=output_path
    return revised
