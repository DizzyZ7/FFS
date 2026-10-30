"""Preflight cost estimates and explicit approval for paid video generation.

No billing, payment or external provider calls are implemented here.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hmac
import math

@dataclass(frozen=True)
class CostEstimate:
    shot_count:int
    total_seconds:float
    estimated_usd:str
    currency:str='USD'
    provider_quote:bool=False

def estimate_generation_cost(blueprint,price_per_second):
    """Operator-entered rate; estimate only, never a vendor quote."""
    try:
        rate=Decimal(str(price_per_second))
    except (InvalidOperation,TypeError) as exc:
        raise ValueError('Invalid rate') from exc
    if not rate.is_finite() or rate<0 or rate>Decimal('1000'):
        raise ValueError('Rate must be between 0 and 1000 USD/second')
    shots=blueprint.get('shots',[])
    if not 1<=len(shots)<=100:
        raise ValueError('Expected 1-100 shots')
    seconds=Decimal('0')
    for shot in shots:
        try:
            duration=Decimal(str(shot['duration']))
        except (KeyError,InvalidOperation,TypeError) as exc:
            raise ValueError('Invalid shot duration') from exc
        if not duration.is_finite() or not Decimal('0')<duration<=Decimal('60'):
            raise ValueError('Shot duration must be 0-60 seconds')
        seconds+=duration
    total=(seconds*rate).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP)
    return CostEstimate(len(shots),float(seconds),str(total))

def validate_paid_generation_approval(*,approved,estimated_usd,max_budget_usd):
    """Explicit approval + hard user budget; reject missing budget and overspend."""
    if approved is not True:
        raise PermissionError('Paid generation requires explicit approval')
    try:
        estimate=Decimal(str(estimated_usd))
        budget=Decimal(str(max_budget_usd))
    except (InvalidOperation,TypeError) as exc:
        raise ValueError('Invalid budget') from exc
    if not estimate.is_finite() or not budget.is_finite() or estimate<0 or budget<0:
        raise ValueError('Invalid budget')
    if estimate>budget:
        raise PermissionError('Estimated generation cost exceeds approved budget')
    return True
