"""Deterministic, inspectable short-form editing plan from source scene ranges."""
import math

FORMATS={'shorts':(1080,1920),'reels':(1080,1920),'tiktok':(1080,1920),
         'landscape':(1920,1080),'square':(1080,1080)}

def create_auto_edit_plan(scenes, duration, *, target_seconds=30,
                          format='reels', pace='dynamic'):
    if format not in FORMATS:
        raise ValueError('Unsupported output format')
    if pace not in ('calm','balanced','dynamic'):
        raise ValueError('Unsupported editing pace')
    if not math.isfinite(target_seconds) or not 3<=target_seconds<=180:
        raise ValueError('Target duration must be 3-180 seconds')
    if not math.isfinite(duration) or duration<=0:
        raise ValueError('Invalid video duration')
    segments=[]
    for i,scene in enumerate(scenes):
        start=float(scene['start']);end=float(scene['end'])
        if not all(map(math.isfinite,(start,end))) or not 0<=start<end<=duration+0.05:
            raise ValueError('Invalid scene boundaries')
        segments.append({'source_index':i,'start':start,'end':min(end,duration)})
    if not segments:
        return {'clips':[],'target_seconds':target_seconds,'estimated_seconds':0,
                'format':format,'resolution':FORMATS[format],'pace':pace,
                'transitions':[]}
    max_clip={'dynamic':3.0,'balanced':5.0,'calm':8.0}[pace]
    remaining=min(target_seconds,sum(x['end']-x['start'] for x in segments))
    clips=[]
    # Sample scenes across the entire source instead of taking only the first N seconds.
    ordered=segments[::2]+segments[1::2]
    while remaining>0.05 and ordered:
        next_round=[]
        for segment in ordered:
            if remaining<=0.05:break
            available=segment['end']-segment['start']
            take=min(available,max_clip,remaining)
            if take<0.05:continue
            clips.append({'start':round(segment['start'],3),'end':round(segment['start']+take,3),
                          'source_index':segment['source_index']})
            segment['start']+=take
            remaining-=take
            if segment['end']-segment['start']>=0.05:
                next_round.append(segment)
        ordered=next_round
    transitions=[{'type':'cut','at_clip':i} for i in range(1,len(clips))]
    return {'clips':clips,'target_seconds':target_seconds,
            'estimated_seconds':round(sum(c['end']-c['start'] for c in clips),3),
            'format':format,'resolution':FORMATS[format],'pace':pace,
            'transitions':transitions}

def create_ranked_auto_edit_plan(ranked_scenes, duration, *, target_seconds=30,
                                 format='reels', pace='dynamic'):
    """Select high-scoring source scenes, then restore source order for coherent playback."""
    if not math.isfinite(target_seconds) or not 3<=target_seconds<=180:
        raise ValueError('Target duration must be 3-180 seconds')
    if not math.isfinite(duration) or duration<=0:
        raise ValueError('Invalid duration')
    if format not in FORMATS or pace not in ('calm','balanced','dynamic'):
        raise ValueError('Invalid format or pace')
    max_clip={'dynamic':3.0,'balanced':5.0,'calm':8.0}[pace]
    selected=[];remaining=target_seconds;seen=set()
    for scene in sorted(ranked_scenes,key=lambda x:(-float(x['score']),float(x['start']))):
        start=float(scene['start']);end=float(scene['end']);score=float(scene['score'])
        index=int(scene['source_index'])
        if (not all(map(math.isfinite,(start,end,score))) or
            not 0<=start<end<=duration+0.05 or not 0<=score<=1 or index in seen):
            raise ValueError('Invalid ranked scene')
        seen.add(index)
        take=min(end-start,max_clip,remaining)
        if take>=0.05:
            selected.append({'start':round(start,3),'end':round(start+take,3),
                             'source_index':index,'score':round(score,4)})
            remaining-=take
        if remaining<0.05:
            break
    selected.sort(key=lambda x:(x['start'],x['source_index']))
    return {'clips':selected,'target_seconds':target_seconds,
            'estimated_seconds':round(sum(c['end']-c['start'] for c in selected),3),
            'format':format,'resolution':FORMATS[format],'pace':pace,
            'ranking_method':'speech_density_and_conciseness',
            'transitions':[{'type':'cut','at_clip':i} for i in range(1,len(selected))]}
