from app.recreation import build_recreation_blueprint,revise_blueprint_shot
from app.recreation_jobs import shot_fingerprint,pending_recreation_shots,mark_shot_generated
import pytest

def blueprint():
    return build_recreation_blueprint({'shots':[{'id':'a','start':0,'end':2},
                                               {'id':'b','start':2,'end':4}]},['subject'],'cinematic')

def test_successful_generation_does_not_dirty_other_shots():
    base=blueprint()
    digest=shot_fingerprint(base['shots'][0])
    updated=mark_shot_generated(base,'a',fingerprint=digest,output_path='generated/a.mp4')
    assert updated['shots'][0]['generation_status']=='succeeded'
    assert [s['id'] for s in pending_recreation_shots(updated)]==['b']
    assert base['shots'][0]['output_path'] is None

def test_stale_output_cannot_override_revision():
    base=blueprint();digest=shot_fingerprint(base['shots'][0])
    changed=revise_blueprint_shot(base,'a',instructions='different actor')
    with pytest.raises(ValueError):
        mark_shot_generated(changed,'a',fingerprint=digest,output_path='generated/a.mp4')
