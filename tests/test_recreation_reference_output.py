import pytest
from app.recreation_reference_output import reference_output_settings

def test_reference_settings_preserve_portrait_and_fractional_fps():
    assert reference_output_settings({'reference':{
        'width':1080,'height':1920,'fps':'30000/1001'}})==(1080,1920,29.97)

def test_reference_settings_default_for_old_blueprints():
    assert reference_output_settings({'shots':[]})==(1280,720,30.0)

def test_reference_settings_reject_oversized_video():
    with pytest.raises(ValueError,match='dimensions'):
        reference_output_settings({'reference':{
            'width':7680,'height':4320,'fps':'30/1'}})

def test_reference_settings_reject_zero_fps():
    with pytest.raises(ValueError,match='FPS'):
        reference_output_settings({'reference':{
            'width':720,'height':1280,'fps':'0/1'}})
