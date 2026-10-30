from fastapi.testclient import TestClient
from app.main import app
from app.provider_config import configured_provider

def test_provider_disabled_by_default():
    result=configured_provider({})
    assert result.provider_id=='disabled'
    assert result.available is False

def test_demo_is_not_ai():
    result=configured_provider({'FFS_GENERATION_PROVIDER':'local-reference-demo'})
    assert result.available is True
    assert 'no AI' in result.reason

def test_unknown_provider_fails_closed():
    result=configured_provider({'FFS_GENERATION_PROVIDER':'unknown'})
    assert result.available is False

def test_provider_status_does_not_claim_ai(monkeypatch):
    monkeypatch.setenv('FFS_GENERATION_PROVIDER','external')
    response=TestClient(app).get('/api/generation/provider')
    assert response.status_code==200
    assert response.json()['supports_ai_generation'] is False
    assert response.json()['available'] is False
