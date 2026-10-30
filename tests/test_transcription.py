import pytest
from pathlib import Path
from app import transcription

def test_rejects_invalid_model(tmp_path):
    source=tmp_path/'clip.mp4'
    source.write_bytes(b'video')
    with pytest.raises(ValueError):
        transcription.transcribe_words(source,model='unknown')

def test_missing_source(tmp_path):
    with pytest.raises(FileNotFoundError):
        transcription.transcribe_words(tmp_path/'missing.mp4')

def test_word_timestamps_without_model_download(tmp_path,monkeypatch):
    source=tmp_path/'clip.mp4'
    source.write_bytes(b'video')
    class Word:
        start=0.1
        end=0.4
        word=' Hello'
    class Segment:
        words=[Word()]
    class Info:
        language='en'
    class FakeModel:
        def transcribe(self,*args,**kwargs):
            assert kwargs['word_timestamps'] is True
            return [Segment()],Info()
    monkeypatch.setattr(transcription,'_model',lambda name:FakeModel())
    result=transcription.transcribe_words(source)
    assert result['words']==[{'start':0.1,'end':0.4,'text':'Hello'}]
    assert result['language']=='en'
