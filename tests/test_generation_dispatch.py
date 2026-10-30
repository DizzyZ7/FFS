import pytest
from app.generation_dispatch import reserve_dispatch,get_dispatch

FP='a'*64

def test_duplicate_key_is_not_reserved_twice(tmp_path):
    first=reserve_dispatch(tmp_path,'key-12345678','shot-0001',FP)
    again=reserve_dispatch(tmp_path,'key-12345678','shot-0001',FP)
    assert first['created'] is True
    assert again['created'] is False
    assert get_dispatch(tmp_path,'key-12345678')['state']=='reserved'

def test_reuse_for_other_revision_rejected(tmp_path):
    reserve_dispatch(tmp_path,'key-12345678','shot-0001',FP)
    with pytest.raises(ValueError):
        reserve_dispatch(tmp_path,'key-12345678','shot-0001','b'*64)

def test_bad_key_rejected(tmp_path):
    with pytest.raises(ValueError):
        reserve_dispatch(tmp_path,'../escape','shot-0001',FP)

@pytest.mark.parametrize('bad_content',['{','[]','{}','{"state":"reserved"}'])
def test_corrupt_reservation_fails_closed(tmp_path,bad_content):
    folder=tmp_path/'generation-dispatch'
    folder.mkdir()
    path=folder/'key-12345678.json'
    path.write_text(bad_content)
    with pytest.raises(ValueError,match='manual reconciliation'):
        reserve_dispatch(tmp_path,'key-12345678','shot-0001',FP)
    with pytest.raises(ValueError,match='manual reconciliation'):
        get_dispatch(tmp_path,'key-12345678')
    assert path.read_text()==bad_content

@pytest.mark.parametrize('record',[
    '{"idempotency_key":"key-12345678","shot_id":"shot-0001","fingerprint":"invalid","state":"reserved"}',
    '{"idempotency_key":"key-12345678","shot_id":"","fingerprint":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","state":"reserved"}'
])
def test_invalid_ledger_identity_fails_closed(tmp_path,record):
    directory=tmp_path/'generation-dispatch'
    directory.mkdir()
    (directory/'key-12345678.json').write_text(record)
    with pytest.raises(ValueError,match='manual reconciliation'):
        reserve_dispatch(tmp_path,'key-12345678','shot-0001',FP)

def test_dispatch_job_binding_is_immutable(tmp_path):
    from app.generation_dispatch import bind_dispatch_job,get_dispatch_job
    reserve_dispatch(tmp_path,'key-12345678','shot-0001',FP)
    first='a'*32
    second='b'*32
    assert bind_dispatch_job(tmp_path,'key-12345678',first)==first
    assert bind_dispatch_job(tmp_path,'key-12345678',first)==first
    with pytest.raises(ValueError,match='another job'):
        bind_dispatch_job(tmp_path,'key-12345678',second)
    assert get_dispatch_job(tmp_path,'key-12345678')==first

def test_invalid_job_binding_fails_closed(tmp_path):
    from app.generation_dispatch import get_dispatch_job
    reserve_dispatch(tmp_path,'key-12345678','shot-0001',FP)
    (tmp_path/'generation-dispatch'/'key-12345678.job').write_text('broken')
    with pytest.raises(ValueError,match='manual reconciliation'):
        get_dispatch_job(tmp_path,'key-12345678')
