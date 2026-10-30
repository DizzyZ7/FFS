import pytest
from app.recreation_render import collect_recreation_clips,render_recreation

def test_recreation_requires_all_shots(tmp_path):
    with pytest.raises(ValueError,match='accepted'):
        collect_recreation_clips(tmp_path,{'shots':[{'generation_status':'not_generated'}]})

def test_recreation_uses_accepted_clips_and_exact_durations(tmp_path,monkeypatch):
    root=tmp_path/'generated';root.mkdir()
    (root/'a.mp4').write_bytes(b'a');(root/'b.mp4').write_bytes(b'b')
    blueprint={'shots':[{'duration':2,'generation_status':'succeeded','output_path':'generated/a.mp4'},
                        {'duration':3,'generation_status':'succeeded','output_path':'generated/b.mp4'}]}
    seen=[]
    def fake_run(args,**kwargs):
        seen.append(args)
    monkeypatch.setattr('app.recreation_render.subprocess.run',fake_run)
    render_recreation(tmp_path,blueprint,tmp_path/'recreation-final.mp4')
    assert len(seen)==1
    filtergraph=seen[0][seen[0].index('-filter_complex')+1]
    assert 'trim=duration=2' in filtergraph
    assert 'trim=duration=3' in filtergraph
    assert 'concat=n=2' in filtergraph

def test_recreation_rejects_escaped_path(tmp_path):
    outside=tmp_path.parent/'outside.mp4';outside.write_bytes(b'x')
    with pytest.raises(ValueError,match='Invalid generated clip'):
        collect_recreation_clips(tmp_path,{'shots':[{
            'duration':2,'generation_status':'succeeded',
            'output_path':'../outside.mp4'}]})
