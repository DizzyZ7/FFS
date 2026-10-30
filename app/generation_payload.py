"""Build immutable, provider-neutral shot payloads before any paid request."""
from dataclasses import dataclass
from .generation import GenerationRequest
from .recreation_jobs import shot_fingerprint

@dataclass(frozen=True)
class PreparedShot:
    request:GenerationRequest
    fingerprint:str

def prepare_shot(blueprint,project_id,shot_id):
    shot=next((s for s in blueprint.get('shots',[]) if s.get('id')==shot_id),None)
    if shot is None:
        raise ValueError('Shot not found')
    if shot.get('generation_status')=='succeeded':
        raise ValueError('Shot already generated; revise before retry')
    request=GenerationRequest(
        project_id=project_id,
        shot_id=shot_id,
        prompt=str(shot.get('instructions','')).strip(),
        duration_seconds=float(shot['duration']),
        subject_ids=tuple(shot.get('subject_ids',[])),
        settings={'reference_start':float(shot['source_start']),
                  'reference_end':float(shot['source_end']),
                  'reference_width':blueprint.get('reference',{}).get('width'),
                  'reference_height':blueprint.get('reference',{}).get('height'),
                  'reference_fps':blueprint.get('reference',{}).get('fps')})
    request.validate()
    return PreparedShot(request=request,fingerprint=shot_fingerprint(shot))

def assert_shot_not_stale(prepared,blueprint):
    current=next((s for s in blueprint.get('shots',[]) if s.get('id')==prepared.request.shot_id),None)
    if current is None or shot_fingerprint(current)!=prepared.fingerprint:
        raise ValueError('Shot changed after preparation')
    return True
