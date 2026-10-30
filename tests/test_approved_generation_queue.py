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
