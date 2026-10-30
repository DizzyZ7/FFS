"""Explicit, safe generation provider selection.

No external provider is enabled implicitly and no secrets are persisted.
"""
import os
from .external_provider import external_provider_settings
from dataclasses import dataclass

@dataclass(frozen=True)
class ProviderConfig:
    provider_id: str
    available: bool
    reason: str

def configured_provider(env=None):
    env=os.environ if env is None else env
    selected=env.get('FFS_GENERATION_PROVIDER','disabled').strip().lower()
    if selected in ('','disabled'):
        return ProviderConfig('disabled',False,'AI generation is disabled by default')
    if selected=='local-reference-demo':
        return ProviderConfig(selected,True,'Demo only: copies source footage, no AI generation')
    if selected=='external':
        return ProviderConfig(selected,False,external_provider_settings(env).reason)
    return ProviderConfig('disabled',False,'Unknown provider setting; generation disabled')
