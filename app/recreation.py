"""Stable reference-recreation blueprint with shot-level asset assignments.

This plans recreation but does not claim to generate video.
"""
import math

def build_recreation_blueprint(reference, subject_ids=(), instructions=''):
    shots=reference.get('shots',[])
    metadata=reference.get('reference',{})
    if not isinstance(instructions,str) or len(instructions)>2000:
        raise ValueError('Instructions must be at most 2000 characters')
    if len(subject_ids)>5 or len(set(subject_ids))!=len(subject_ids):
        raise ValueError('Provide up to five distinct subjects')
    if not shots or len(shots)>100:
        raise ValueError('Reference must have 1-100 shots')
    timeline=[];previous=0.0
    for index,shot in enumerate(shots):
        start=float(shot['start']);end=float(shot['end'])
        if not all(map(math.isfinite,(start,end))) or start<0 or start<previous-0.001 or end<=start:
            raise ValueError('Invalid reference shot timings')
        previous=end
        timeline.append({
            'id':shot.get('id') or f'shot-{index+1:04d}',
            'source_start':round(start,3),'source_end':round(end,3),
            'duration':round(end-start,3),
            'subject_ids':list(subject_ids),
            'instructions':instructions.strip(),
            'generation_status':'not_generated',
            'revision':0,
            'output_path':None
        })
    return {'schema_version':1,'mode':'reference_recreation',
            'reference':{'duration':round(previous,3),
                         'width':metadata.get('width'),'height':metadata.get('height'),
                         'fps':metadata.get('fps')},
            'shots':timeline,'cut_points':[x['source_end'] for x in timeline[:-1]],
            'generation_available':False,
            'warning':'Blueprint only: video generation provider not configured'}

def revise_blueprint_shot(blueprint,shot_id,*,instructions=None,subject_ids=None):
    if instructions is None and subject_ids is None:
        raise ValueError('Specify at least one change')
    if instructions is not None and (not isinstance(instructions,str) or len(instructions)>2000):
        raise ValueError('Invalid instructions')
    if subject_ids is not None and (len(subject_ids)>5 or len(set(subject_ids))!=len(subject_ids)):
        raise ValueError('Invalid subjects')
    import copy
    revised=copy.deepcopy(blueprint)
    match=next((s for s in revised['shots'] if s['id']==shot_id),None)
    if match is None:
        raise ValueError('Shot not found')
    if instructions is not None:
        match['instructions']=instructions.strip()
    if subject_ids is not None:
        match['subject_ids']=list(subject_ids)
    match['revision']=int(match.get('revision',0))+1
    match['generation_status']='not_generated'
    match['output_path']=None
    return revised
