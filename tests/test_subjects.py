import io
import tempfile
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from app import main

client=TestClient(main.app)

def test_subject_library_rejects_invalid_images():
    pid='a'*32
    with tempfile.TemporaryDirectory() as d:
        (Path(d)/pid).mkdir()
        with patch.object(main,'ROOT',Path(d)):
            assert client.get('/api/projects/'+pid+'/subjects').json()=={'subjects':[]}
            r=client.post('/api/projects/'+pid+'/subjects',
                data={'name':'Hero'},files={'file':('bad.png',b'not an image','image/png')})
            assert r.status_code==415
            r=client.post('/api/projects/'+pid+'/subjects',
                data={'name':'Hero'},files={'file':('big.png',b'\\x89PNG\\r\\n\\x1a\\n'+b'0'*(5*1024*1024),'image/png')})
            assert r.status_code==413
            assert client.get('/api/projects/'+pid+'/subjects').json()=={'subjects':[]}

def test_subject_library_rejects_invalid_names():
    pid='b'*32
    with tempfile.TemporaryDirectory() as d:
        (Path(d)/pid).mkdir()
        with patch.object(main,'ROOT',Path(d)):
            r=client.post('/api/projects/'+pid+'/subjects',
                data={'name':'  '},files={'file':('a.jpg',b'\\xff\\xd8\\xff','image/jpeg')})
            assert r.status_code==422
