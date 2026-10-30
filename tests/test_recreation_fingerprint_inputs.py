from app.recreation_jobs import shot_fingerprint

def test_fingerprint_changes_for_reference_timing():
    shot={'id':'shot-1','duration':2,'source_start':0,'source_end':2,
          'revision':0,'subject_ids':[],'instructions':'A',
          'generation_status':'not_generated','output_path':None}
    original=shot_fingerprint(shot)
    changed=dict(shot,source_start=1,source_end=3)
    assert shot_fingerprint(changed)!=original

def test_fingerprint_changes_for_future_generation_settings():
    shot={'id':'shot-1','duration':2,'revision':0,'instructions':'A'}
    changed=dict(shot,camera_motion='orbit')
    assert shot_fingerprint(changed)!=shot_fingerprint(shot)

def test_fingerprint_does_not_change_on_acceptance_metadata():
    shot={'id':'shot-1','duration':2,'revision':0,'instructions':'A',
          'generation_status':'not_generated','output_path':None}
    accepted=dict(shot,generation_status='succeeded',output_path='generated/a.mp4')
    assert shot_fingerprint(accepted)==shot_fingerprint(shot)
