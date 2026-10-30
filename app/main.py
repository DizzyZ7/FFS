import json
import os
import re
import shutil
import uuid
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .media import probe, detect_scenes, render
from .reference import reference_plan, extract_contact_sheet_frames

ROOT=Path(os.environ.get('FRAMEFORGE_DATA','./data')).resolve()
ROOT.mkdir(parents=True,exist_ok=True)
MAX_BYTES=500*1024*1024
app=FastAPI(title='FrameForge Studio',version='0.1.0')

class Clip(BaseModel):
    start: float
    end: float

class RenderRequest(BaseModel):
    clips: list[Clip]

class ShotNote(BaseModel):
    shot_id: str = Field(pattern=r'^shot-[0-9]{4}

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
        project={'id':pid,'filename':Path(file.filename or 'video.mp4').name,'metadata':meta,'scenes':scenes,'timeline':scenes,'revision':1}
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

@app.put('/api/projects/{pid}/timeline')
def save_timeline(pid:str,request:TimelineRequest):
    folder=project_dir(pid)
    path=folder/'project.json'
    project=json.loads(path.read_text(encoding='utf8'))
    duration=float(project['metadata']['duration'])
    clips=[c.model_dump() for c in request.clips]
    if any(not (0<=c['start']<c['end']<=duration+0.01) for c in clips):
        raise HTTPException(422,'Invalid timeline bounds')
    project['timeline']=clips
    project['revision']=project.get('revision',1)+1
    temp=folder/'project.json.tmp'
    temp.write_text(json.dumps(project),encoding='utf8')
    temp.replace(path)
    return {'revision':project['revision'],'timeline':clips}

@app.get('/api/projects/{pid}/shot-plan')
def get_shot_plan(pid:str):
    folder=project_dir(pid)
    path=folder/'shot-plan.json'
    if path.is_file():
        return json.loads(path.read_text(encoding='utf8'))
    return reference_plan(folder/'source.mp4')

@app.put('/api/projects/{pid}/shot-plan')
def save_shot_plan(pid:str,request:ShotPlanRequest):
    folder=project_dir(pid)
    path=folder/'shot-plan.json'
    plan=json.loads(path.read_text(encoding='utf8')) if path.is_file() else reference_plan(folder/'source.mp4')
    by_id={shot['id']:shot for shot in plan['shots']}
    if len(request.shots)!=len({shot.shot_id for shot in request.shots}):
        raise HTTPException(422,'Duplicate shot IDs')
    for item in request.shots:
        if item.shot_id not in by_id:
            raise HTTPException(422,'Unknown shot ID')
        if len(set(item.subject_ids))!=len(item.subject_ids) or any(not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}',x) for x in item.subject_ids):
            raise HTTPException(422,'Invalid subject IDs')
    for item in request.shots:
        by_id[item.shot_id]['prompt']=item.prompt
        by_id[item.shot_id]['subject_ids']=item.subject_ids
    plan['revision']=plan.get('revision',0)+1
    temp=folder/'shot-plan.json.tmp'
    temp.write_text(json.dumps(plan),encoding='utf8')
    temp.replace(path)
    return plan

@app.get('/api/projects/{pid}/analysis')
def get_analysis(pid:str,threshold:float=0.30):
    folder=project_dir(pid)
    try:
        return reference_plan(folder/'source.mp4',threshold)
    except ValueError as e:
        raise HTTPException(422,str(e)) from e
    except Exception as e:
        raise HTTPException(500,'Reference analysis failed') from e

@app.post('/api/projects/{pid}/storyboard')
def generate_storyboard(pid:str):
    folder=project_dir(pid)
    try:
        plan=reference_plan(folder/'source.mp4')
        images=extract_contact_sheet_frames(folder/'source.mp4',folder/'storyboard',plan['shots'])
        plan['preview_frames']=[{'shot_id':plan['shots'][i]['id'],'url':f'/api/projects/{pid}/storyboard/{name}'} for i,name in enumerate(images)]
        return plan
    except Exception as e:
        raise HTTPException(500,'Storyboard generation failed') from e

@app.get('/api/projects/{pid}/storyboard/{filename}')
def storyboard_frame(pid:str,filename:str):
    if not re.fullmatch(r'shot-[0-9]{4}\.jpg',filename):
        raise HTTPException(400,'Invalid frame name')
    path=project_dir(pid)/'storyboard'/filename
    if not path.is_file():
        raise HTTPException(404,'Frame not found')
    return FileResponse(path,media_type='image/jpeg')

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
)
    prompt: str = Field(default='', max_length=2000)
    subject_ids: list[str] = Field(default_factory=list, max_length=5)

class ShotPlanRequest(BaseModel):
    shots: list[ShotNote] = Field(max_length=100)

class TimelineRequest(BaseModel):
    clips: list[Clip] = Field(max_length=100)

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
        project={'id':pid,'filename':Path(file.filename or 'video.mp4').name,'metadata':meta,'scenes':scenes,'timeline':scenes,'revision':1}
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

@app.put('/api/projects/{pid}/timeline')
def save_timeline(pid:str,request:TimelineRequest):
    folder=project_dir(pid)
    path=folder/'project.json'
    project=json.loads(path.read_text(encoding='utf8'))
    duration=float(project['metadata']['duration'])
    clips=[c.model_dump() for c in request.clips]
    if any(not (0<=c['start']<c['end']<=duration+0.01) for c in clips):
        raise HTTPException(422,'Invalid timeline bounds')
    project['timeline']=clips
    project['revision']=project.get('revision',1)+1
    temp=folder/'project.json.tmp'
    temp.write_text(json.dumps(project),encoding='utf8')
    temp.replace(path)
    return {'revision':project['revision'],'timeline':clips}

@app.get('/api/projects/{pid}/analysis')
def get_analysis(pid:str,threshold:float=0.30):
    folder=project_dir(pid)
    try:
        return reference_plan(folder/'source.mp4',threshold)
    except ValueError as e:
        raise HTTPException(422,str(e)) from e
    except Exception as e:
        raise HTTPException(500,'Reference analysis failed') from e

@app.post('/api/projects/{pid}/storyboard')
def generate_storyboard(pid:str):
    folder=project_dir(pid)
    try:
        plan=reference_plan(folder/'source.mp4')
        images=extract_contact_sheet_frames(folder/'source.mp4',folder/'storyboard',plan['shots'])
        plan['preview_frames']=[{'shot_id':plan['shots'][i]['id'],'url':f'/api/projects/{pid}/storyboard/{name}'} for i,name in enumerate(images)]
        return plan
    except Exception as e:
        raise HTTPException(500,'Storyboard generation failed') from e

@app.get('/api/projects/{pid}/storyboard/{filename}')
def storyboard_frame(pid:str,filename:str):
    if not re.fullmatch(r'shot-[0-9]{4}\.jpg',filename):
        raise HTTPException(400,'Invalid frame name')
    path=project_dir(pid)/'storyboard'/filename
    if not path.is_file():
        raise HTTPException(404,'Frame not found')
    return FileResponse(path,media_type='image/jpeg')

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
)
    prompt: str = Field(default='', max_length=2000)
    subject_ids: list[str] = Field(default_factory=list, max_length=5)

class ShotPlanRequest(BaseModel):
    shots: list[ShotNote] = Field(max_length=100)

class TimelineRequest(BaseModel):
    clips: list[Clip] = Field(max_length=100)

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
        project={'id':pid,'filename':Path(file.filename or 'video.mp4').name,'metadata':meta,'scenes':scenes,'timeline':scenes,'revision':1}
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

@app.put('/api/projects/{pid}/timeline')
def save_timeline(pid:str,request:TimelineRequest):
    folder=project_dir(pid)
    path=folder/'project.json'
    project=json.loads(path.read_text(encoding='utf8'))
    duration=float(project['metadata']['duration'])
    clips=[c.model_dump() for c in request.clips]
    if any(not (0<=c['start']<c['end']<=duration+0.01) for c in clips):
        raise HTTPException(422,'Invalid timeline bounds')
    project['timeline']=clips
    project['revision']=project.get('revision',1)+1
    temp=folder/'project.json.tmp'
    temp.write_text(json.dumps(project),encoding='utf8')
    temp.replace(path)
    return {'revision':project['revision'],'timeline':clips}

@app.get('/api/projects/{pid}/shot-plan')
def get_shot_plan(pid:str):
    folder=project_dir(pid)
    path=folder/'shot-plan.json'
    if path.is_file():
        return json.loads(path.read_text(encoding='utf8'))
    return reference_plan(folder/'source.mp4')

@app.put('/api/projects/{pid}/shot-plan')
def save_shot_plan(pid:str,request:ShotPlanRequest):
    folder=project_dir(pid)
    path=folder/'shot-plan.json'
    plan=json.loads(path.read_text(encoding='utf8')) if path.is_file() else reference_plan(folder/'source.mp4')
    by_id={shot['id']:shot for shot in plan['shots']}
    if len(request.shots)!=len({shot.shot_id for shot in request.shots}):
        raise HTTPException(422,'Duplicate shot IDs')
    for item in request.shots:
        if item.shot_id not in by_id:
            raise HTTPException(422,'Unknown shot ID')
        if len(set(item.subject_ids))!=len(item.subject_ids) or any(not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}',x) for x in item.subject_ids):
            raise HTTPException(422,'Invalid subject IDs')
    for item in request.shots:
        by_id[item.shot_id]['prompt']=item.prompt
        by_id[item.shot_id]['subject_ids']=item.subject_ids
    plan['revision']=plan.get('revision',0)+1
    temp=folder/'shot-plan.json.tmp'
    temp.write_text(json.dumps(plan),encoding='utf8')
    temp.replace(path)
    return plan

@app.get('/api/projects/{pid}/analysis')
def get_analysis(pid:str,threshold:float=0.30):
    folder=project_dir(pid)
    try:
        return reference_plan(folder/'source.mp4',threshold)
    except ValueError as e:
        raise HTTPException(422,str(e)) from e
    except Exception as e:
        raise HTTPException(500,'Reference analysis failed') from e

@app.post('/api/projects/{pid}/storyboard')
def generate_storyboard(pid:str):
    folder=project_dir(pid)
    try:
        plan=reference_plan(folder/'source.mp4')
        images=extract_contact_sheet_frames(folder/'source.mp4',folder/'storyboard',plan['shots'])
        plan['preview_frames']=[{'shot_id':plan['shots'][i]['id'],'url':f'/api/projects/{pid}/storyboard/{name}'} for i,name in enumerate(images)]
        return plan
    except Exception as e:
        raise HTTPException(500,'Storyboard generation failed') from e

@app.get('/api/projects/{pid}/storyboard/{filename}')
def storyboard_frame(pid:str,filename:str):
    if not re.fullmatch(r'shot-[0-9]{4}\.jpg',filename):
        raise HTTPException(400,'Invalid frame name')
    path=project_dir(pid)/'storyboard'/filename
    if not path.is_file():
        raise HTTPException(404,'Frame not found')
    return FileResponse(path,media_type='image/jpeg')

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
)
    prompt: str = Field(default='', max_length=2000)
    subject_ids: list[str] = Field(default_factory=list, max_length=5)

class ShotPlanRequest(BaseModel):
    shots: list[ShotNote] = Field(max_length=100)

class TimelineRequest(BaseModel):
    clips: list[Clip] = Field(max_length=100)

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
        project={'id':pid,'filename':Path(file.filename or 'video.mp4').name,'metadata':meta,'scenes':scenes,'timeline':scenes,'revision':1}
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

@app.put('/api/projects/{pid}/timeline')
def save_timeline(pid:str,request:TimelineRequest):
    folder=project_dir(pid)
    path=folder/'project.json'
    project=json.loads(path.read_text(encoding='utf8'))
    duration=float(project['metadata']['duration'])
    clips=[c.model_dump() for c in request.clips]
    if any(not (0<=c['start']<c['end']<=duration+0.01) for c in clips):
        raise HTTPException(422,'Invalid timeline bounds')
    project['timeline']=clips
    project['revision']=project.get('revision',1)+1
    temp=folder/'project.json.tmp'
    temp.write_text(json.dumps(project),encoding='utf8')
    temp.replace(path)
    return {'revision':project['revision'],'timeline':clips}

@app.get('/api/projects/{pid}/analysis')
def get_analysis(pid:str,threshold:float=0.30):
    folder=project_dir(pid)
    try:
        return reference_plan(folder/'source.mp4',threshold)
    except ValueError as e:
        raise HTTPException(422,str(e)) from e
    except Exception as e:
        raise HTTPException(500,'Reference analysis failed') from e

@app.post('/api/projects/{pid}/storyboard')
def generate_storyboard(pid:str):
    folder=project_dir(pid)
    try:
        plan=reference_plan(folder/'source.mp4')
        images=extract_contact_sheet_frames(folder/'source.mp4',folder/'storyboard',plan['shots'])
        plan['preview_frames']=[{'shot_id':plan['shots'][i]['id'],'url':f'/api/projects/{pid}/storyboard/{name}'} for i,name in enumerate(images)]
        return plan
    except Exception as e:
        raise HTTPException(500,'Storyboard generation failed') from e

@app.get('/api/projects/{pid}/storyboard/{filename}')
def storyboard_frame(pid:str,filename:str):
    if not re.fullmatch(r'shot-[0-9]{4}\.jpg',filename):
        raise HTTPException(400,'Invalid frame name')
    path=project_dir(pid)/'storyboard'/filename
    if not path.is_file():
        raise HTTPException(404,'Frame not found')
    return FileResponse(path,media_type='image/jpeg')

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
