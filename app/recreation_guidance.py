"""Deterministic generation guidance from measured reference metadata.

This is advisory metadata, not an AI-generated description of scene content.
"""
def build_shot_guidance(blueprint,*,motion_scenes=None,audio_onsets=None):
    shots=blueprint.get('shots',[])
    if len(shots)>100:
        raise ValueError('Too many shots')
    motion_scenes=motion_scenes or []
    audio_onsets=audio_onsets or []
    guidance=[]
    for i,shot in enumerate(shots):
        start=float(shot['source_start'])
        end=float(shot['source_end'])
        duration=float(shot['duration'])
        if not 0<=start<end or duration<=0:
            raise ValueError('Invalid shot timings')
        motion=motion_scenes[i] if i<len(motion_scenes) else {}
        activity=motion.get('visual_activity','unknown')
        if activity not in ('low','medium','high','unknown'):
            activity='unknown'
        near_start=any(abs(float(t)-start)<=0.12 for t in audio_onsets)
        near_end=any(abs(float(t)-end)<=0.12 for t in audio_onsets)
        guidance.append({
            'shot_id':shot['id'],'duration_seconds':round(duration,3),
            'reference_start':round(start,3),'reference_end':round(end,3),
            'visual_activity':activity,
            'camera_motion':'unknown',
            'onset_near_start':near_start,'onset_near_end':near_end,
            'subject_ids':shot.get('subject_ids',[]),
            'user_instructions':shot.get('instructions',''),
            'generation_guidance':(
                f"Generate a {duration:.3f}-second shot. "
                f"Match the reference shot timing ({start:.3f}-{end:.3f}s). "
                f"Reference frame-change activity: {activity} (not camera direction). "
                f"{'A musical onset occurs near the beginning. ' if near_start else ''}"
                f"{'A musical onset occurs near the ending cut. ' if near_end else ''}"
                f"User instructions: {shot.get('instructions','')}"
            ),
            'limitations':'Camera motion, transitions and scene semantics are not inferred.'
        })
    return {'shots':guidance,'method':'deterministic_reference_guidance'}
