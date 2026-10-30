"""Opt-in, local speech transcription using faster-whisper.

Install separately: pip install faster-whisper
Model weights are downloaded on first use unless a local model directory is supplied.
"""
from pathlib import Path
from functools import lru_cache
import math

SUPPORTED_MODELS = frozenset({'tiny', 'base', 'small'})

@lru_cache(maxsize=2)
def _model(name: str):
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError('Offline transcription unavailable: install faster-whisper') from exc
    return WhisperModel(name, device='cpu', compute_type='int8')

def transcribe_words(source: Path, model: str='tiny', language: str|None=None):
    if model not in SUPPORTED_MODELS:
        raise ValueError('Unsupported transcription model')
    if language is not None and (len(language) not in (2,3) or not language.isalpha()):
        raise ValueError('Invalid language code')
    if not source.is_file():
        raise FileNotFoundError('Video not found')
    segments, info = _model(model).transcribe(
        str(source), language=language, word_timestamps=True,
        vad_filter=True, beam_size=3)
    words=[]
    for segment in segments:
        for word in segment.words or []:
            start=float(word.start)
            end=float(word.end)
            text=word.word.strip()
            if not (math.isfinite(start) and math.isfinite(end)) or start<0 or end<=start or not text:
                continue
            words.append({'start':round(start,3),'end':round(end,3),'text':text})
            if len(words)>3000:
                raise ValueError('Transcription exceeds 3000 words')
    return {'language':info.language,'words':words,'model':model}
