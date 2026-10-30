from app.reference_motion import parse_scene_differences,classify_activity

def test_parse_scdet_scores():
    log='[Parsed_metadata_3] lavfi.scd.score=0.32\n[Parsed_metadata_3] lavfi.scd.score=6.5'
    assert parse_scene_differences(log)==[0.32,6.5]

def test_activity_thresholds():
    assert classify_activity([])=='unknown'
    assert classify_activity([0.1,0.4])=='low'
    assert classify_activity([3.0])=='medium'
    assert classify_activity([7.0])=='high'
