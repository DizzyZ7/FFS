import pytest
from app.approved_generation_queue import queue_approved_shot

def blueprint():
    return {'shots':[{'id':'shot-0001','duration':2,'source_start':0,'source_end':2,
                      'instructions':'Sunrise','subject_ids':[],'revision':0,
                      'generation_status':'not_generated'}]}

def test_approval_and_idempotent_queue(tmp_path):
    args=dict(price_per_second_usd=2,approved=True,max_budget_usd=4)
    first=queue_approved_shot(tmp_path,blueprint(),'project','shot-0001','key-12345678',**args)
    second=queue_approved_shot(tmp_path,blueprint(),'project','shot-0001','key-12345678',**args)
    assert first['job']['id']==second['job']['id']
    assert second['reservation']['created'] is False

def test_budget_rejects_before_reservation(tmp_path):
    with pytest.raises(PermissionError):
        queue_approved_shot(tmp_path,blueprint(),'project','shot-0001','key-12345678',
                            price_per_second_usd=2,approved=True,max_budget_usd=1)
    assert not (tmp_path/'generation-dispatch').exists()

def test_no_approval_rejected(tmp_path):
    with pytest.raises(PermissionError):
        queue_approved_shot(tmp_path,blueprint(),'project','shot-0001','key-12345678',
                            price_per_second_usd=2,approved=False,max_budget_usd=4)

def test_reserved_without_job_does_not_retry_automatically(tmp_path):
    from app.generation_dispatch import reserve_dispatch
    from app.generation_preflight import prepare_generation_batch
    batch=prepare_generation_batch(blueprint(),'project',['shot-0001'],
        price_per_second_usd=2,approved=True,max_budget_usd=4)
    reserve_dispatch(tmp_path,'key-12345678','shot-0001',batch.fingerprints[0])
    result=queue_approved_shot(tmp_path,blueprint(),'project','shot-0001','key-12345678',
        price_per_second_usd=2,approved=True,max_budget_usd=4)
    assert result['job'] is None
    assert 'manual reconciliation' in result['warning']
    assert not (tmp_path/'generation-jobs').exists()

def test_conflicting_key_after_edit_rejected(tmp_path):
    args=dict(price_per_second_usd=2,approved=True,max_budget_usd=4)
    queue_approved_shot(tmp_path,blueprint(),'project','shot-0001','key-12345678',**args)
    changed=blueprint()
    changed['shots'][0]['instructions']='Different sunrise'
    with pytest.raises(ValueError,match='reused'):
        queue_approved_shot(tmp_path,changed,'project','shot-0001','key-12345678',**args)

def test_replay_never_matches_unrelated_job(tmp_path):
    from app import jobs
    from app.generation_dispatch import reserve_dispatch
    from app.generation_preflight import prepare_generation_batch
    batch=prepare_generation_batch(blueprint(),'project',['shot-0001'],
        price_per_second_usd=2,approved=True,max_budget_usd=4)
    jobs.enqueue(tmp_path,'shot-0001',fingerprint=batch.fingerprints[0])
    reserve_dispatch(tmp_path,'key-12345678','shot-0001',batch.fingerprints[0])
    result=queue_approved_shot(tmp_path,blueprint(),'project','shot-0001','key-12345678',
        price_per_second_usd=2,approved=True,max_budget_usd=4)
    assert result['job'] is None

def test_bound_job_identity_survives_replay(tmp_path):
    from app.generation_dispatch import get_dispatch_job
    args=dict(price_per_second_usd=2,approved=True,max_budget_usd=4)
    first=queue_approved_shot(tmp_path,blueprint(),'project','shot-0001','key-12345678',**args)
    assert get_dispatch_job(tmp_path,'key-12345678')==first['job']['id']
    replay=queue_approved_shot(tmp_path,blueprint(),'project','shot-0001','key-12345678',**args)
    assert replay['job']['id']==first['job']['id']
