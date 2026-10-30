from app.reference_audio import cut_alignment, audio_onsets

def test_cut_alignment_with_nearest_onsets():
    result=cut_alignment([1.0,2.0,3.0],[0.95,2.4,3.08],tolerance=0.12)
    assert result['aligned_count']==2
    assert result['cuts'][0]['offset_seconds']==-0.05
    assert result['cuts'][1]['nearest_onset'] is None

def test_silent_reference_has_no_onsets(monkeypatch,tmp_path):
    monkeypatch.setattr('app.reference_audio._audio_samples',lambda _:[])
    result=audio_onsets(tmp_path/'silent.mp4')
    assert result['has_audio'] is False
    assert result['onsets']==[]
