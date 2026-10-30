"""Side-effect-free generation batch preflight; never dispatches paid requests."""
from dataclasses import dataclass
from .generation_budget import select_shots_for_estimate,estimate_generation_cost,validate_paid_generation_approval
from .generation_payload import prepare_shot,assert_shot_not_stale

@dataclass(frozen=True)
class GenerationBatchPreflight:
    shot_ids:tuple[str,...]
    fingerprints:tuple[str,...]
    estimated_usd:str
    total_seconds:float
    approved:bool

def prepare_generation_batch(blueprint,project_id,shot_ids,*,price_per_second_usd,
                             approved=False,max_budget_usd=None):
    selected=select_shots_for_estimate(blueprint,shot_ids)
    prepared=tuple(prepare_shot(blueprint,project_id,shot['id'])
                   for shot in selected['shots'])
    estimate=estimate_generation_cost(selected,price_per_second_usd)
    if approved:
        validate_paid_generation_approval(approved=True,
            estimated_usd=estimate.estimated_usd,max_budget_usd=max_budget_usd)
    return GenerationBatchPreflight(
        tuple(item.request.shot_id for item in prepared),
        tuple(item.fingerprint for item in prepared),
        estimate.estimated_usd,estimate.total_seconds,approved is True)

def validate_generation_batch(batch,blueprint,project_id):
    for shot_id,fingerprint in zip(batch.shot_ids,batch.fingerprints):
        prepared=prepare_shot(blueprint,project_id,shot_id)
        if prepared.fingerprint!=fingerprint:
            raise ValueError('Generation batch stale: a shot changed')
    return True
