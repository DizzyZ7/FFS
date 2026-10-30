# Contributing to FFS

Thank you for contributing to FrameForge Studio.

## Quick start

- Install Python 3.11+, FFmpeg and ffprobe.
- Create a virtual environment and run `pip install -r requirements.txt`.
- Install test dependencies with `pip install pytest httpx`.
- Run `python -m pytest -q` and `python scripts/smoke_render.py`.
- Run `uvicorn app.main:app --host 127.0.0.1 --port 8000`.

## Pull requests

1. Open an issue for substantial architectural changes.
2. Work on a feature branch; keep PRs focused.
3. Add tests for changed behavior and update docs.
4. Do not commit media, model weights, API keys or generated outputs.
5. Explain backwards compatibility, migrations and resource usage.
6. Keep CI green before merging.

## Licensing

Code contributions are submitted under the repository's MIT license.
Only contribute code/assets you own or are licensed to redistribute.
Keep third-party copyright notices and license files when required.
Do not copy private model weights, proprietary prompts, private API endpoints or copyrighted presets.

## AI and safety

Remote upload must be opt-in. Never silently incur generation costs.
Obtain permission for likenesses, source videos and audio. Report vulnerabilities privately to the maintainers; do not post exploit details in public issues.
