from app.recreation_guidance import build_shot_guidance

def test_guidance_uses_reference_timing_audio_and_activity():
    blueprint={'shots':[{'id':'shot-0001','source_start':0,'source_end':2,
                          'duration':2,'subject_ids':['subject-1'],
                          'instructions':'Use red jacket'}]}
    result=build_shot_guidance(blueprint,motion_scenes=[
        {'visual_activity':'high'}],audio_onsets=[0.05,1.95])
    shot=result['shots'][0]
    assert shot['onset_near_start'] and shot['onset_near_end']
    assert shot['visual_activity']=='high'
    assert shot['camera_motion']=='unknown'
    assert 'red jacket' in shot['generation_guidance']
