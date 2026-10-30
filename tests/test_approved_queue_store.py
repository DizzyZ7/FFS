import pytest
from app.approved_queue_store import reserve_approved_job

FP='a'*64

def test_atomic_replay_returns_same_job(tmp_path):
    first=reserve_approved_job(tmp_path,'key-12345678','shot-0001',FP)
    replay=reserve_approved_job(tmp_path,'key-12345678','shot-0001',FP)
    assert first['created'] is True
    assert replay['created'] is False
    assert first['job']['id']==replay['job']['id']

def test_atomic_replay_rejects_changed_revision(tmp_path):
    reserve_approved_job(tmp_path,'key-12345678','shot-0001',FP)
    with pytest.raises(ValueError,match='reused'):
        reserve_approved_job(tmp_path,'key-12345678','shot-0001','b'*64)

def test_atomic_store_survives_reopen(tmp_path):
    first=reserve_approved_job(tmp_path,'key-12345678','shot-0001',FP)
    assert (tmp_path/'approved-queue.sqlite3').is_file()
    second=reserve_approved_job(tmp_path,'key-12345678','shot-0001',FP)
    assert first['job']==second['job']
