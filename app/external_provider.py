"""Fail-closed external provider configuration without network side effects."""
import os
from dataclasses import dataclass
from urllib.parse import urlsplit

@dataclass(frozen=True)
class ExternalProviderSettings:
    endpoint:str
    model:str
    credential_present:bool
    enabled:bool
    reason:str

def external_provider_settings(env=None):
    env=os.environ if env is None else env
    enabled=env.get('FFS_EXTERNAL_ENABLED','').lower()=='true'
    endpoint=env.get('FFS_EXTERNAL_ENDPOINT','').strip()
    model=env.get('FFS_EXTERNAL_MODEL','').strip()
    token=env.get('FFS_EXTERNAL_API_KEY','')
    try:
        parsed=urlsplit(endpoint)
        valid=(parsed.scheme=='https' and bool(parsed.hostname)
               and not parsed.username and not parsed.password
               and parsed.port in (None,443)
               and not parsed.fragment and not parsed.query
               and parsed.hostname.lower() not in ('localhost','127.0.0.1','::1')
               and '.' in parsed.hostname)
    except ValueError:
        valid=False
    if not enabled:
        reason='External provider disabled by default'
    elif not valid:
        reason='A public HTTPS provider endpoint is required'
    elif not model or len(model)>128:
        reason='A model identifier is required'
    elif not token:
        reason='Provider API key is missing'
    else:
        reason='Configuration ready; no external adapter installed'
    return ExternalProviderSettings(endpoint if valid else '',model if len(model)<=128 else '',
                                    bool(token),enabled,reason)
