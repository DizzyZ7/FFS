import json
import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .media import probe, detect_scenes, render, render_social
from .reference import reference_plan, extract_contact_sheet_frames
from .recreation import build_recreation_blueprint, revise_blueprint_shot
from .recreation_render import render_recreation
from .recreation_jobs import shot_fingerprint, pending_recreation_shots
from .recreation_accept import accept_completed_job
from . import jobs
from .transcription import transcribe_words
from .speech_cuts import plan_speech_cuts
from .auto_edit import create_auto_edit_plan, create_ranked_auto_edit_plan
from .edit_instructions import parse_edit_request
from .highlights import rank_highlights
from .visual_analysis import visual_scene_scores
from .captions import Word, save_ass, render_captioned_video

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
    shot_id: str = Field(pattern=r'^shot-[0-9]{4}$')
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
    subject_manifest=folder/'subjects.json'
    known_subjects={x['id'] for x in json.loads(subject_manifest.read_text(encoding='utf8')).get('subjects',[])} if subject_manifest.is_file() else set()
    for item in request.shots:
        if any(subject_id not in known_subjects for subject_id in item.subject_ids):
            raise HTTPException(422,'Unknown subject ID')
    for item in request.shots:
        by_id[item.shot_id]['prompt']=item.prompt
        by_id[item.shot_id]['subject_ids']=item.subject_ids
    plan['revision']=plan.get('revision',0)+1
    temp=folder/'shot-plan.json.tmp'
    temp.write_text(json.dumps(plan),encoding='utf8')
    temp.replace(path)
    return plan

@app.get('/api/projects/{pid}/subjects')
def list_subjects(pid:str):
    folder=project_dir(pid)
    path=folder/'subjects.json'
    if not path.is_file():
        return {'subjects':[]}
    return json.loads(path.read_text(encoding='utf8'))

@app.post('/api/projects/{pid}/subjects')
async def add_subject(pid:str,file:UploadFile=File(...),name:str=Form(...)):
    folder=project_dir(pid)
    name=name.strip()
    if not 1<=len(name)<=80:
        raise HTTPException(422,'Subject name must contain 1–80 characters')
    data=await file.read(5*1024*1024+1)
    if len(data)>5*1024*1024:
        raise HTTPException(413,'Subject image exceeds 5 MB')
    # Verify file signatures rather than trusting browser-supplied MIME types.
    if data.startswith(bytes.fromhex('89504e470d0a1a0a')):
        extension='png';mime='image/png'
    elif data.startswith(bytes.fromhex('ffd8ff')):
        extension='jpg';mime='image/jpeg'
    elif data.startswith(b'RIFF') and data[8:12]==b'WEBP':
        extension='webp';mime='image/webp'
    else:
        raise HTTPException(415,'Only PNG, JPEG and WebP are supported')
    import subprocess
    subject_id=uuid.uuid4().hex
    assets=folder/'subjects'
    assets.mkdir(exist_ok=True)
    target=assets/(subject_id+'.'+extension)
    target.write_bytes(data)
    try:
        result=subprocess.run(['ffprobe','-v','error','-select_streams','v:0',
            '-show_entries','stream=width,height','-of','json',str(target)],
            capture_output=True,text=True,timeout=15)
        if result.returncode:
            raise ValueError('Invalid image')
        streams=json.loads(result.stdout).get('streams',[])
        if not streams:
            raise ValueError('Invalid image')
        width=int(streams[0]['width']);height=int(streams[0]['height'])
        if not 1<=width<=8192 or not 1<=height<=8192 or width*height>24000000:
            raise ValueError('Image dimensions out of range')
    except (ValueError,KeyError,TypeError,subprocess.SubprocessError,OSError):
        target.unlink(missing_ok=True)
        raise HTTPException(422,'Image cannot be decoded or is too large')
    path=folder/'subjects.json'
    manifest=json.loads(path.read_text(encoding='utf8')) if path.is_file() else {'subjects':[]}
    if len(manifest['subjects'])>=100:
        target.unlink(missing_ok=True)
        raise HTTPException(422,'Maximum 100 subjects per project')
    item={'id':subject_id,'name':name,'image_url':f'/api/projects/{pid}/subjects/{subject_id}/image',
          'mime_type':mime,'width':width,'height':height}
    manifest['subjects'].append(item)
    temp=folder/'subjects.json.tmp'
    temp.write_text(json.dumps(manifest),encoding='utf8')
    temp.replace(path)
    return item

@app.get('/api/projects/{pid}/subjects/{subject_id}/image')
def subject_image(pid:str,subject_id:str):
    if not re.fullmatch(r'[0-9a-f]{32}',subject_id):
        raise HTTPException(400,'Invalid subject ID')
    folder=project_dir(pid)
    manifest=list_subjects(pid)
    item=next((x for x in manifest['subjects'] if x['id']==subject_id),None)
    if item is None:
        raise HTTPException(404,'Subject not found')
    extension={'image/png':'png','image/jpeg':'jpg','image/webp':'webp'}.get(item['mime_type'])
    if extension is None:
        raise HTTPException(500,'Invalid subject metadata')
    return FileResponse(folder/'subjects'/(subject_id+'.'+extension),media_type=item['mime_type'])

@app.post('/api/projects/{pid}/generation/jobs')
def enqueue_generation(pid:str,shot_id:str):
    folder=project_dir(pid)
    plan_path=folder/'shot-plan.json'
    plan=json.loads(plan_path.read_text(encoding='utf8')) if plan_path.is_file() else reference_plan(folder/'source.mp4')
    shot=next((item for item in plan['shots'] if item['id']==shot_id),None)
    if shot is None:
        raise HTTPException(404,'Shot not found')
    if not str(shot.get('prompt','')).strip():
        raise HTTPException(422,'Set a shot prompt before queuing generation')
    # Deliberately no provider call. This records intent only.
    return jobs.enqueue(folder,shot_id)

@app.get('/api/projects/{pid}/generation/jobs')
def list_generation_jobs(pid:str):
    return {'jobs':jobs.list_jobs(project_dir(pid))}

@app.get('/api/projects/{pid}/generation/jobs/{job_id}')
def get_generation_job(pid:str,job_id:str):
    try:
        return jobs.get_job(project_dir(pid),job_id)
    except ValueError as exc:
        raise HTTPException(400,str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(404,'Job not found') from exc

@app.post('/api/projects/{pid}/generation/jobs/{job_id}/cancel')
def cancel_generation_job(pid:str,job_id:str):
    try:
        return jobs.cancel(project_dir(pid),job_id)
    except ValueError as exc:
        raise HTTPException(409,str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(404,'Job not found') from exc

class RecreationBlueprintRequest(BaseModel):
    subject_ids: list[str] = Field(default_factory=list,max_length=5)
    instructions: str = Field(default='',max_length=2000)

class RecreationShotRevision(BaseModel):
    instructions: str|None = Field(default=None,max_length=2000)
    subject_ids: list[str]|None = Field(default=None,max_length=5)

@app.post('/api/projects/{pid}/recreation/blueprint')
def create_recreation_blueprint(pid:str,request:RecreationBlueprintRequest):
    folder=project_dir(pid)
    shot_path=folder/'shot-plan.json'
    plan=json.loads(shot_path.read_text(encoding='utf8')) if shot_path.is_file() else reference_plan(folder/'source.mp4')
    try:
        blueprint=build_recreation_blueprint(plan,request.subject_ids,request.instructions)
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc
    dest=folder/'recreation-blueprint.json'
    temp=folder/'recreation-blueprint.json.tmp'
    temp.write_text(json.dumps(blueprint,ensure_ascii=False,indent=2),encoding='utf8')
    temp.replace(dest)
    return blueprint

@app.get('/api/projects/{pid}/recreation/blueprint')
def get_recreation_blueprint(pid:str):
    path=project_dir(pid)/'recreation-blueprint.json'
    if not path.is_file():
        raise HTTPException(404,'Recreation blueprint not created')
    return json.loads(path.read_text(encoding='utf8'))

@app.patch('/api/projects/{pid}/recreation/shots/{shot_id}')
def revise_recreation_shot(pid:str,shot_id:str,request:RecreationShotRevision):
    folder=project_dir(pid)
    path=folder/'recreation-blueprint.json'
    if not path.is_file():
        raise HTTPException(404,'Recreation blueprint not created')
    try:
        revised=revise_blueprint_shot(json.loads(path.read_text(encoding='utf8')),
            shot_id,instructions=request.instructions,subject_ids=request.subject_ids)
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc
    temp=folder/'recreation-blueprint.json.tmp'
    temp.write_text(json.dumps(revised,ensure_ascii=False,indent=2),encoding='utf8')
    temp.replace(path)
    return revised

@app.get('/api/projects/{pid}/recreation/pending')
def get_pending_recreation_shots(pid:str):
    blueprint=get_recreation_blueprint(pid)
    return {'shots':pending_recreation_shots(blueprint)}

@app.post('/api/projects/{pid}/recreation/shots/{shot_id}/queue')
def queue_recreation_shot(pid:str,shot_id:str):
    folder=project_dir(pid)
    blueprint=get_recreation_blueprint(pid)
    shot=next((s for s in blueprint['shots'] if s['id']==shot_id),None)
    if shot is None:
        raise HTTPException(404,'Shot not found')
    if not shot.get('instructions','').strip():
        raise HTTPException(422,'Set instructions before queuing the shot')
    fingerprint=shot_fingerprint(shot)
    for existing in jobs.list_jobs(folder):
        if (existing['shot_id']==shot_id and existing.get('fingerprint')==fingerprint
                and existing['status'] in ('queued','running')):
            return existing
    return jobs.enqueue(folder,shot_id,fingerprint=fingerprint)

@app.post('/api/projects/{pid}/recreation/jobs/{job_id}/accept')
def accept_recreation_job(pid:str,job_id:str):
    folder=project_dir(pid)
    try:
        return accept_completed_job(folder,job_id)
    except FileNotFoundError as exc:
        raise HTTPException(404,'Job or blueprint not found') from exc
    except ValueError as exc:
        raise HTTPException(409,str(exc)) from exc

@app.post('/api/projects/{pid}/recreation/render')
def render_recreated_video(pid:str):
    folder=project_dir(pid)
    blueprint=get_recreation_blueprint(pid)
    try:
        render_recreation(folder,blueprint,folder/'recreation-final.mp4')
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc
    except (subprocess.SubprocessError,OSError) as exc:
        raise HTTPException(503,'Could not assemble recreation video') from exc
    return {'download_url':f'/api/projects/{pid}/recreation/download',
            'warning':'Video-only 720p render; no audio or transitions yet'}

@app.get('/api/projects/{pid}/recreation/download')
def download_recreated_video(pid:str):
    output=project_dir(pid)/'recreation-final.mp4'
    if not output.is_file():
        raise HTTPException(404,'Recreated video not rendered')
    return FileResponse(output,media_type='video/mp4',filename='recreation.mp4')

@app.get('/api/projects/{pid}/visual-scores')
def visual_scores(pid:str):
    folder=project_dir(pid)
    project=json.loads((folder/'project.json').read_text(encoding='utf8'))
    try:
        scores=visual_scene_scores(folder/'source.mp4',project['scenes'],
                                   duration=float(project['metadata']['duration']))
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(503,'Visual analysis unavailable') from exc
    return {'scenes':scores,'method':'ffmpeg_brightness',
            'warning':'Exposure heuristic only; not semantic or aesthetic scoring'}

class RankedAutoEditRequest(BaseModel):
    model: str = 'tiny'
    language: str|None = None
    target_seconds: float = Field(default=30,ge=3,le=180)
    format: str = 'reels'
    pace: str = 'dynamic'

@app.post('/api/projects/{pid}/auto-edit/ranked-plan')
def ranked_auto_edit_plan(pid:str,request:RankedAutoEditRequest):
    folder=project_dir(pid)
    project=json.loads((folder/'project.json').read_text(encoding='utf8'))
    try:
        transcript=transcribe_words(folder/'source.mp4',model=request.model,language=request.language)
        ranked=rank_highlights(project['scenes'],transcript['words'],
                               duration=float(project['metadata']['duration']))
        plan=create_ranked_auto_edit_plan(ranked,float(project['metadata']['duration']),
                 target_seconds=request.target_seconds,format=request.format,pace=request.pace)
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(503,'Speech analysis unavailable') from exc
    return {'plan':plan,'ranked_scenes':ranked,
            'warning':'Highlight ranking is heuristic; inspect before export'}

class HighlightRequest(BaseModel):
    model: str = 'tiny'
    language: str|None = None

@app.post('/api/projects/{pid}/highlights')
def highlights(pid:str,request:HighlightRequest):
    folder=project_dir(pid)
    project=json.loads((folder/'project.json').read_text(encoding='utf8'))
    try:
        transcript=transcribe_words(folder/'source.mp4',model=request.model,language=request.language)
        ranked=rank_highlights(project['scenes'],transcript['words'],
                               duration=float(project['metadata']['duration']))
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(503,'Speech analysis unavailable') from exc
    return {'ranked_scenes':ranked,'ranking_method':'speech_density_and_conciseness',
            'warning':'Heuristic scores; not semantic quality or emotion detection'}

class EditInstructionRequest(BaseModel):
    instruction: str = Field(min_length=1,max_length=1000)

@app.post('/api/projects/{pid}/auto-edit/instruction')
def auto_edit_instruction(pid:str,request:EditInstructionRequest):
    folder=project_dir(pid)
    project=json.loads((folder/'project.json').read_text(encoding='utf8'))
    try:
        settings=parse_edit_request(request.instruction)
        plan=create_auto_edit_plan(project['scenes'],float(project['metadata']['duration']),
            target_seconds=settings['target_seconds'],format=settings['format'],
            pace=settings['pace'])
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc
    return {'plan':plan,'interpreted':settings}

class SocialRenderRequest(BaseModel):
    clips: list[Clip] = Field(min_length=1,max_length=100)
    aspect: str = '9:16'
    framing: str = 'crop'

@app.post('/api/projects/{pid}/social-render')
def social_render(pid:str,request:SocialRenderRequest):
    folder=project_dir(pid)
    try:
        render_social(folder/'source.mp4',[c.model_dump() for c in request.clips],
                      folder/'social-output.mp4',aspect=request.aspect,framing=request.framing)
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500,'Social export failed') from exc
    return {'download':f'/api/projects/{pid}/social-download'}

@app.get('/api/projects/{pid}/social-download')
def social_download(pid:str):
    path=project_dir(pid)/'social-output.mp4'
    if not path.is_file():
        raise HTTPException(404,'Social export not found')
    return FileResponse(path,filename='frameforge-social.mp4',media_type='video/mp4')

class AutoEditPlanRequest(BaseModel):
    target_seconds: float = Field(default=30,ge=3,le=180)
    format: str = 'reels'
    pace: str = 'dynamic'

@app.post('/api/projects/{pid}/auto-edit/plan')
def auto_edit_plan(pid:str,request:AutoEditPlanRequest):
    folder=project_dir(pid)
    project=json.loads((folder/'project.json').read_text(encoding='utf8'))
    try:
        return create_auto_edit_plan(project['scenes'],float(project['metadata']['duration']),
                                     target_seconds=request.target_seconds,
                                     format=request.format,pace=request.pace)
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc

class SpeechCutRequest(BaseModel):
    model: str = 'tiny'
    language: str|None = None
    min_pause: float = Field(default=0.65,ge=0.1,le=10)
    padding: float = Field(default=0.18,ge=0,le=2)

@app.post('/api/projects/{pid}/speech-cuts/preview')
def speech_cut_preview(pid:str,request:SpeechCutRequest):
    folder=project_dir(pid)
    project=json.loads((folder/'project.json').read_text(encoding='utf8'))
    try:
        transcript=transcribe_words(folder/'source.mp4',model=request.model,language=request.language)
        clips=plan_speech_cuts(transcript['words'],float(project['metadata']['duration']),
                               min_pause=request.min_pause,padding=request.padding)
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(503,'Transcription unavailable') from exc
    duration=sum(clip['end']-clip['start'] for clip in clips)
    return {'clips':clips,'source_duration':project['metadata']['duration'],
            'edited_duration':round(duration,3),'words':len(transcript['words'])}

class AutoCaptionRequest(BaseModel):
    model: str = Field(default='tiny')
    language: str|None = None
    style: str = Field(default='pop')
    max_words: int = Field(default=4,ge=1,le=12)

@app.post('/api/projects/{pid}/auto-captions')
def auto_captions(pid:str,request:AutoCaptionRequest):
    folder=project_dir(pid)
    if request.style not in ('pop','minimal','bold'):
        raise HTTPException(422,'Unknown caption style')
    try:
        result=transcribe_words(folder/'source.mp4',model=request.model,language=request.language)
        words=[Word(**w) for w in result['words']]
        if not words:
            raise HTTPException(422,'No spoken words detected')
        save_ass(folder/'captions.ass',words,request.style,request.max_words)
        render_captioned_video(folder/'source.mp4',folder/'captioned.mp4',folder/'captions.ass')
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(503,'Caption processing unavailable or failed') from exc
    return {'download':f'/api/projects/{pid}/auto-captions/download','word_count':len(words),'language':result['language']}

@app.get('/api/projects/{pid}/auto-captions/download')
def download_auto_captions(pid:str):
    path=project_dir(pid)/'captioned.mp4'
    if not path.is_file():
        raise HTTPException(404,'Captioned render not found')
    return FileResponse(path,filename='frameforge-auto-captions.mp4',media_type='video/mp4')

@app.post('/api/projects/{pid}/transcription')
def transcribe_project(pid:str,model:str='tiny',language:str|None=None):
    folder=project_dir(pid)
    try:
        return transcribe_words(folder/'source.mp4',model=model,language=language)
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(503,str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(404,'Source video not found') from exc

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
