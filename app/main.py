import json
import os
import re
import shutil
import uuid
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from .media import probe, detect_scenes, render

ROOT=Path(os.environ.get('FRAMEFORGE_DATA','./data')).resolve()
ROOT.mkdir(parents=True,exist_ok=True)
MAX_BYTES=500*1024*1024
app=FastAPI(title='FrameForge Studio',version='0.1.0')

class Clip(BaseModel):
    start: float
    end: float

class RenderRequest(BaseModel):
    clips: list[Clip]

def project_dir(pid):
    if not re.fullmatch(r'[0-9a-f]{32}',pid):
        raise HTTPException(400,'Invalid project id')
    d=ROOT/pid
    if not d.is_dir():
        raise HTTPException(404,'Project not found')
    return d

@app.get('/api/health')
def health():
    return {'status':'ok','ffmpeg':shutil.which('ffmpeg') is not None,'ffprobe':shutil.which('ffprobe') is not None}

@app.post('/api/projects')
async def create_project(file:UploadFile=File(...)):
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        raise HTTPException(503,'FFmpeg and ffprobe must be installed')
    pid=uuid.uuid4().hex
    folder=ROOT/pid
    folder.mkdir()
    source=folder/'source.mp4'
    count=0
    try:
        with source.open('wb') as target:
            while chunk:=await file.read(1024*1024):
                count+=len(chunk)
                if count>MAX_BYTES:
                    raise HTTPException(413,'File exceeds 500 MB')
                target.write(chunk)
        meta=probe(source)
        if meta['duration']<=0 or meta['duration']>600:
            raise HTTPException(400,'Video duration must be 0–600 seconds')
        scenes=detect_scenes(source,meta['duration'])
        project={'id':pid,'filename':Path(file.filename or 'video.mp4').name,'metadata':meta,'scenes':scenes}
        (folder/'project.json').write_text(json.dumps(project),encoding='utf8')
        return project
    except HTTPException:
        shutil.rmtree(folder,ignore_errors=True)
        raise
    except Exception as e:
        shutil.rmtree(folder,ignore_errors=True)
        raise HTTPException(400,'Unable to decode video') from e

@app.get('/api/projects/{pid}')
def get_project(pid:str):
    return json.loads((project_dir(pid)/'project.json').read_text(encoding='utf8'))

@app.get('/api/projects/{pid}/source')
def source(pid:str):
    return FileResponse(project_dir(pid)/'source.mp4',media_type='video/mp4')

@app.post('/api/projects/{pid}/render')
def export(pid:str,request:RenderRequest):
    folder=project_dir(pid)
    try:
        render(folder/'source.mp4',[c.model_dump() for c in request.clips],folder/'output.mp4')
    except (ValueError,RuntimeError) as e:
        raise HTTPException(400,str(e)) from e
    except Exception as e:
        raise HTTPException(500,'Render failed; inspect FFmpeg installation') from e
    return {'download':f'/api/projects/{pid}/download'}

@app.get('/api/projects/{pid}/download')
def download(pid:str):
    path=project_dir(pid)/'output.mp4'
    if not path.exists():
        raise HTTPException(404,'Render not found')
    return FileResponse(path,filename='frameforge-export.mp4',media_type='video/mp4')

app.mount('/',StaticFiles(directory=str(Path(__file__).parent.parent/'web'),html=True),name='web')
