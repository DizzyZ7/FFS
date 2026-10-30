from pathlib import Path
from unittest.mock import patch
import pytest
from app.reference import reference_plan, _validate_threshold

@pytest.mark.parametrize('value',[-1,0,1,float('nan'),float('inf')])
def test_invalid_threshold(value):
    with pytest.raises(ValueError):
        _validate_threshold(value)

@patch('app.reference.detect_scenes',return_value=[{'start':0.0,'end':2.0},{'start':2.0,'end':5.0}])
@patch('app.reference.probe',return_value={'duration':5.0,'width':1920,'height':1080})
def test_reference_plan(probe_mock,scene_mock):
    plan=reference_plan(Path('reference.mp4'))
    assert plan['schema_version']==1
    assert plan['analysis']['shot_count']==2
    assert plan['shots'][0]['id']=='shot-0001'
    assert plan['shots'][1]['duration']==3.0
    assert all(s['status']=='not_generated' for s in plan['shots'])
