# FrameForge Studio (FFS)

**Open-source, local-first reference-video analysis and editing studio.** Turn a video reference into a structured shot plan, inspect storyboard frames, edit a clip timeline, and export locally with FFmpeg.

[![CI](https://github.com/DizzyZ7/FFS/actions/workflows/ci.yml/badge.svg)](https://github.com/DizzyZ7/FFS/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)

> **Early alpha:** FFS does **not** currently generate new AI video, replace actors, or match music beats. These are roadmap goals, not shipped features. It is not affiliated with Higgsfield.

## Why FFS?

- **Local-first:** analyze references and export clips without uploading videos to a cloud service.
- **Inspectable:** scene boundaries, structured shot plans and preview frames.
- **Editable:** save and reopen timeline selections.
- **Open:** MIT-licensed code, contributor guidelines and public development roadmap.
- **Provider-independent future:** opt-in AI video adapters with explicit cost estimates.

## What works today?

| Capability | Status |
| --- | --- |
| Upload video references | Available (500 MB / 10 min limit) |
| FFmpeg scene detection | Available |
| Reference shot plan | Available |
| Storyboard JPEG extraction | API available |
| Browser timeline selection | Basic |
| Timeline persistence | Available |
| Local 720p MP4 export | Available (silent) |
| Multi-track audio editing | Planned |
| Generative subject replacement | Planned |
| Prompt-driven scene regeneration | Planned |

## Quick start

Requirements: Python 3.11+, FFmpeg and ffprobe installed on your PATH.

```bash
git clone https://github.com/DizzyZ7/FFS.git
cd FFS
python -m venv .venv
# Activate: Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000** and upload a short reference video.

### API overview

- `GET /api/health` — service status
- `POST /api/projects` — upload a reference
- `GET /api/projects/{id}` — project metadata and timeline
- `PUT /api/projects/{id}/timeline` — save clip ranges
- `GET /api/projects/{id}/analysis` — shot plan
- `POST /api/projects/{id}/storyboard` — extract shot previews
- `POST /api/projects/{id}/render` — render selected clips
- `GET /api/projects/{id}/download` — download rendered MP4

## Tests

```bash
pip install pytest httpx
python -m pytest -q
python scripts/smoke_render.py
```

CI also runs on pull requests.

## Project direction

We are building an **open, reference-driven video creation pipeline**: reference analysis → storyboard → subject library → optional generative shots → selective revisions → editable final timeline.

See [technical specification](docs/KATANA_PARITY_SPEC.md), [architecture](docs/ARCHITECTURE.md) and [roadmap](docs/ROADMAP.md). This is a long-term engineering goal, not a claim of feature parity with proprietary tools.

## Contribute

Issues, testing, documentation and pull requests are welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md), review [SECURITY.md](SECURITY.md) and browse the [roadmap](docs/ROADMAP.md). If FFS is useful to you, consider starring the repository so others can discover it.

## Privacy and license

FFS is an unauthenticated local prototype. **Do not expose its HTTP server to the public internet.** Only use reference media and identities you have permission to process. Code is released under the [MIT License](LICENSE).
