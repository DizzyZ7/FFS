"""Explicitly approved, idempotent local queueing; no paid execution."""
from . import jobs
from .generation_preflight import prepare_generation_batch
from .generation_dispatch import reserve_dispatch

def queue_approved_shot(folder,blueprint,project_id,shot_id,idempotency_key,
                        *,price_per_second_usd,approved,max_budget_usd):
    batch=prepare_generation_batch(
        blueprint,project_id,[shot_id],price_per_second_usd=price_per_second_usd,
        approved=approved,max_budget_usd=max_budget_usd)
    if batch.approved is not True:
        raise PermissionError('Explicit approval required for this queue')
    fingerprint=batch.fingerprints[0]
    reservation=reserve_dispatch(folder,idempotency_key,shot_id,fingerprint)
    # Never create another job when the same reservation key is replayed.
    existing=[job for job in jobs.list_jobs(folder)
              if job['shot_id']==shot_id and job.get('fingerprint')==fingerprint]
    if not reservation['created']:
        if existing:
            return {'reservation':reservation,'job':existing[0]}
        return {'reservation':reservation,'job':None,
                'warning':'Existing reservation requires manual reconciliation'}
    if existing:
        return {'reservation':reservation,'job':existing[0]}
    return {'reservation':reservation,'job':jobs.enqueue(folder,shot_id,fingerprint=fingerprint)}
