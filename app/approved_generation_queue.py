"""Explicitly approved, idempotent local queueing; no paid execution."""
from . import jobs
from .generation_preflight import prepare_generation_batch
from .generation_dispatch import reserve_dispatch, bind_dispatch_job, get_dispatch_job

def queue_approved_shot(folder,blueprint,project_id,shot_id,idempotency_key,
                        *,price_per_second_usd,approved,max_budget_usd):
    batch=prepare_generation_batch(
        blueprint,project_id,[shot_id],price_per_second_usd=price_per_second_usd,
        approved=approved,max_budget_usd=max_budget_usd)
    if batch.approved is not True:
        raise PermissionError('Explicit approval required for this queue')
    fingerprint=batch.fingerprints[0]
    reservation=reserve_dispatch(folder,idempotency_key,shot_id,fingerprint)
    bound_id=get_dispatch_job(folder,idempotency_key)
    if not reservation['created']:
        if bound_id is None:
            return {'reservation':reservation,'job':None,
                    'warning':'Existing reservation requires manual reconciliation'}
        try:
            bound=jobs.get_job(folder,bound_id)
        except FileNotFoundError:
            return {'reservation':reservation,'job':None,
                    'warning':'Bound job missing; manual reconciliation required'}
        if bound['shot_id']!=shot_id or bound.get('fingerprint')!=fingerprint:
            raise ValueError('Bound job identity differs from reservation')
        return {'reservation':reservation,'job':bound}
    # A newly created reservation is the only path that may enqueue.
    # A crash between enqueue and binding requires manual reconciliation.
    job=jobs.enqueue(folder,shot_id,fingerprint=fingerprint)
    bind_dispatch_job(folder,idempotency_key,job['id'])
    return {'reservation':reservation,'job':job}
