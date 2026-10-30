# FFS architecture

FFS is a local-first video-reference editor. It does not require a GPU or remote API for scene analysis and basic export.

## Current modules

- `app/main.py`: HTTP API, upload limits, project metadata, media download.
- `app/media.py`: ffprobe metadata, FFmpeg scene detection, deterministic MP4 rendering.
- `web/index.html`: minimal browser UI for upload, timeline clip selection and export.
- `data/<uuid>/`: local project source, metadata and rendered output (ignored by Git).
- `tests/`: unit/API tests.
- `scripts/smoke_render.py`: synthetic-video end-to-end smoke test.

## Planned modules

- `app/projects/`: project revisions, clip ordering, persistent timelines, migrations.
- `app/jobs/`: asynchronous render queue, cancellation and progress.
- `app/providers/`: opt-in AI providers with cost confirmation and explicit upload consent.
- `web/editor/`: multitrack timeline, audio, waveform and storyboard.

## Safety and limits

- Loopback-only default server binding; do not expose this API to the public internet.
- 500 MB upload and 10-minute input video limit.
- Project IDs are random UUID hex strings.
- AI upload is opt-in; no paid model is currently connected.
- Rendering is synchronous in v0.1; long renders block the request.

## Local development

Install Python 3.11+, FFmpeg/ffprobe, then:

```bash
python -m venv .venv
pip install -r requirements.txt
python -m pytest -q
python scripts/smoke_render.py
uvicorn app.main:app --host 127.0.0.1 --port 8000
```
