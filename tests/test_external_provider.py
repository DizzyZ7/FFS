from app.external_provider import external_provider_settings
from app.provider_config import configured_provider

def test_external_disabled_by_default():
    assert external_provider_settings({}).enabled is False

def test_external_rejects_local_endpoint():
    config=external_provider_settings({'FFS_EXTERNAL_ENABLED':'true',
        'FFS_EXTERNAL_ENDPOINT':'http://127.0.0.1:8000',
        'FFS_EXTERNAL_MODEL':'model','FFS_EXTERNAL_API_KEY':'secret'})
    assert config.endpoint==''
    assert 'HTTPS' in config.reason

def test_external_config_never_exposes_secret():
    env={'FFS_GENERATION_PROVIDER':'external','FFS_EXTERNAL_ENABLED':'true',
        'FFS_EXTERNAL_ENDPOINT':'https://api.example.com/v1/generate',
        'FFS_EXTERNAL_MODEL':'model','FFS_EXTERNAL_API_KEY':'super-secret'}
    assert 'super-secret' not in repr(external_provider_settings(env))
    assert 'super-secret' not in repr(configured_provider(env))
    assert configured_provider(env).available is False
