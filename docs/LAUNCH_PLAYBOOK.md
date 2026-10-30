# Ethical launch playbook for FFS

## North-star metric

Weekly active users who successfully import a reference and export a video. Stars and forks are useful discovery signals, not substitutes for product quality.

## Before announcing

- CI green and a reproducible install on Windows, Linux and macOS.
- 30–60 second demo recording of **real** current functionality, not AI-generated mockups.
- Two sample reference clips with confirmed redistribution licenses and a benchmark test.
- README screenshot, API docs, known limitations and 3–5 good first issues.
- First version tag and changelog after the release has been tested.

## Distribution channels

1. GitHub: accurate description, topics, social preview and release notes.
2. Hacker News: Show HN post once the demo and installer work; engage with feedback, avoid repeated submissions.
3. Reddit: share only in relevant communities that allow self-promotion, with a useful technical write-up and disclosure that you maintain the project.
4. Dev.to/Hashnode: explain FFmpeg scene detection, shot plan format, and reproducible benchmark methodology.
5. YouTube: short demonstration and technical walkthrough.
6. AI/video developer communities: request feedback, not stars-for-stars.

## Suggested GitHub topics

`video-editor`, `ffmpeg`, `fastapi`, `video-processing`, `open-source`, `storyboard`, `scene-detection`, `local-first`, `python`, `ai-video`.

The `ai-video` tag refers to the project direction; explicitly mark generative features as planned.

## Measurement

Track weekly (manually or through GitHub Insights):
- Unique visitors and clone counts (where GitHub provides them)
- Stars and forks, by week
- Issues from new contributors
- First successful installs
- User-reported export success
- Retention and feature requests

Do not buy stars, use bots, spam communities, or misrepresent feature completeness.

## Launch post draft

**Title:** FrameForge Studio — open-source local-first reference video analyzer and editor (early alpha)

**Body:** I am building FrameForge Studio, an MIT-licensed FastAPI/FFmpeg project for breaking down reference videos into editable shot plans. Today it supports scene detection, storyboard frame extraction via API, timeline persistence and basic silent 720p export. It does not yet generate AI video. The long-term goal is a provider-agnostic reference-to-video workflow with per-shot regeneration. I would love feedback on the shot-plan schema, cross-platform setup and media test coverage. Source: https://github.com/DizzyZ7/FFS
