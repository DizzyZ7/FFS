import copy
import pytest
from app.generation_preflight import prepare_generation_batch,validate_generation_batch

def blueprint():
    return {'shots':[{'id':'shot-0001','duration':2,'source_start':0,'source_end':2,
             'instructions':'Sunrise','subject_ids':[],'revision':0,'generation_status':'not_generated'},
             {'id':'shot-0002','duration':3,'source_start':2,'source_end':5,
             'instructions':'Ocean','subject_ids':[],'revision':0,'generation_status':'not_generated'}]}

def test_batch_selects_only_requested_shot():
    batch=prepare_generation_batch(blueprint(),'project',['shot-0002'],
                                  price_per_second_usd='0.5')
    assert batch.shot_ids==('shot-0002',)
    assert batch.estimated_usd=='1.50'
    assert batch.approved is False
    assert validate_generation_batch(batch,blueprint(),'project')

def test_batch_budget_and_revision_guard():
    with pytest.raises(PermissionError):
        prepare_generation_batch(blueprint(),'project',['shot-0001'],
                                 price_per_second_usd=2,approved=True,max_budget_usd=1)
    batch=prepare_generation_batch(blueprint(),'project',['shot-0001'],
                                  price_per_second_usd=2,approved=True,max_budget_usd=4)
    changed=copy.deepcopy(blueprint())
    changed['shots'][0]['instructions']='Changed'
    with pytest.raises(ValueError):
        validate_generation_batch(batch,changed,'project')
