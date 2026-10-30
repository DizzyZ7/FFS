"""Fingerprint the exact accepted recreation inputs used for final export."""
import hashlib
import json

def export_fingerprint(blueprint):
    shots=blueprint.get('shots',[])
    if not shots:
        raise ValueError('No recreation shots')
    payload=[{
        'id':shot['id'],
        'revision':shot['revision'],
        'duration':shot['duration'],
        'generation_status':shot.get('generation_status'),
        'output_path':shot.get('output_path'),
        'instructions':shot.get('instructions'),
        'subject_ids':shot.get('subject_ids'),
    } for shot in shots]
    data=json.dumps(payload,sort_keys=True,ensure_ascii=False,separators=(',',':'))
    return hashlib.sha256(data.encode('utf8')).hexdigest()
