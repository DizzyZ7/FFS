"""Provider-neutral generation contract. No network or paid API calls are made."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

class JobStatus(str, Enum):
    queued = 'queued'
    running = 'running'
    succeeded = 'succeeded'
    failed = 'failed'
    cancelled = 'cancelled'

@dataclass(frozen=True)
class GenerationRequest:
    project_id: str
    shot_id: str
    prompt: str
    duration_seconds: float
    subject_ids: tuple[str, ...] = ()
    settings: dict = field(default_factory=dict)

    def validate(self) -> None:
        if not self.prompt.strip() or len(self.prompt)>2000:
            raise ValueError('Prompt must be 1–2000 characters')
        if not 0 < self.duration_seconds <= 60:
            raise ValueError('Shot duration must be between 0 and 60 seconds')
        if len(self.subject_ids)>5:
            raise ValueError('Maximum five subject references')

@dataclass(frozen=True)
class GenerationResult:
    status: JobStatus
    output_path: str | None = None
    error: str | None = None

class GenerationProvider(Protocol):
    @property
    def provider_id(self) -> str: ...

    def generate(self, request: GenerationRequest) -> GenerationResult: ...

class DisabledProvider:
    """Safe placeholder; explicitly refuses generation until configured."""
    provider_id = 'disabled'

    def generate(self, request: GenerationRequest) -> GenerationResult:
        request.validate()
        return GenerationResult(
            status=JobStatus.failed,
            error='No AI generation provider is configured. Local video editing remains available.',
        )
