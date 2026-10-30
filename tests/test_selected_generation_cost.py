import pytest
from app.generation_budget import select_shots_for_estimate,estimate_generation_cost

BLUEPRINT={'shots':[{'id':'shot-0001','duration':2},{'id':'shot-0002','duration':4}]}

def test_selected_scene_only_is_billed():
    selected=select_shots_for_estimate(BLUEPRINT,['shot-0002'])
    result=estimate_generation_cost(selected,'0.50')
    assert result.shot_count==1
    assert result.estimated_usd=='2.00'

def test_unknown_and_duplicate_shots_are_rejected():
    with pytest.raises(ValueError):
        select_shots_for_estimate(BLUEPRINT,['missing'])
    with pytest.raises(ValueError):
        select_shots_for_estimate(BLUEPRINT,['shot-0001','shot-0001'])
