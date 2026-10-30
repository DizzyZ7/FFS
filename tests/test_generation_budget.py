import pytest
from app.generation_budget import estimate_generation_cost,validate_paid_generation_approval

def test_cost_estimate_rounds_currency():
    result=estimate_generation_cost({'shots':[{'duration':2.5},{'duration':1.5}]},'0.12')
    assert result.estimated_usd=='0.48'
    assert result.total_seconds==4.0
    assert result.provider_quote is False

def test_paid_generation_requires_explicit_approval_and_budget():
    with pytest.raises(PermissionError):
        validate_paid_generation_approval(approved=False,estimated_usd='2',max_budget_usd='5')
    with pytest.raises(PermissionError):
        validate_paid_generation_approval(approved=True,estimated_usd='6',max_budget_usd='5')
    assert validate_paid_generation_approval(approved=True,estimated_usd='2',max_budget_usd='5')

def test_invalid_rate_rejected():
    with pytest.raises(ValueError):
        estimate_generation_cost({'shots':[{'duration':1}]},float('nan'))
