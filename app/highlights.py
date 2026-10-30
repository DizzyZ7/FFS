"""Explainable highlight scoring from visual cuts and word density.

Scores are heuristics, not emotional or semantic understanding.
"""
import math

def rank_highlights(scenes, words, *, duration):
    if not math.isfinite(duration) or duration<=0:
        raise ValueError('Invalid duration')
    clean=[]
    for i,scene in enumerate(scenes):
        start=float(scene['start']);end=float(scene['end'])
        if not all(map(math.isfinite,(start,end))) or not 0<=start<end<=duration+0.05:
            raise ValueError('Invalid scene')
        clean.append((i,start,min(end,duration)))
    timed=[]
    for word in words:
        start=float(word['start']);end=float(word['end'])
        if not all(map(math.isfinite,(start,end))) or not 0<=start<end<=duration+0.05:
            raise ValueError('Invalid word')
        timed.append((start,end))
    results=[]
    for i,start,end in clean:
        length=end-start
        spoken=sum(max(0,min(end,b)-max(start,a)) for a,b in timed)
        speech_ratio=min(1.0,spoken/length)
        # Prefer coherent, concise scenes; a rapid-cut sequence receives a modest boost.
        concise=min(1.0,5.0/max(length,0.05))
        score=round(0.65*speech_ratio+0.35*concise,4)
        results.append({'source_index':i,'start':round(start,3),'end':round(end,3),
                        'score':score,'signals':{'speech_coverage':round(speech_ratio,3),
                                                'conciseness':round(concise,3)}})
    return sorted(results,key=lambda x:(-x['score'],x['start']))
