from dataclasses import FrozenInstanceError
import pytest
from app.generation import (
    DisabledProvider, GenerationRequest, JobStatus,
)

def make_request(**kwargs):
    data=dict(project_id='p',shot_id='shot-0001',prompt='cinematic tracking shot',
              duration_seconds=5.0)
    data.update(kwargs)
    return GenerationRequest(**data)

def test_disabled_provider_fails_without_side_effects():
    result=DisabledProvider().generate(make_request())
    assert result.status==JobStatus.failed
    assert result.output_path is None
    assert 'No AI generation provider' in result.error

@pytest.mark.parametrize('kwargs',[
    {'prompt':' '},
    {'prompt':'x'*2001},
    {'duration_seconds':0},
    {'duration_seconds':61},
    {'subject_ids':tuple(str(i) for i in range(6))},
])
def test_invalid_generation_request(kwargs):
    with pytest.raises(ValueError):
        make_request(**kwargs).validate()

def test_request_is_immutable():
    with pytest.raises(FrozenInstanceError):
        make_request().prompt='modified'
