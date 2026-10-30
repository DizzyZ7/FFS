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
