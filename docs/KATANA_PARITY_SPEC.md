# FFS — Reference-Driven Video Generation: Product Specification

Status: research-based specification, not a claim of feature parity.

## Sources reviewed (2026-10-30)

- Official Higgsfield Katana help: https://higgsfield.ai/creator-hub/help-center/integrations/how-do-i-use-katana
- Official Katana overview: https://higgsfield.ai/blog/higgsfield-katana
- Higgsfield MCP: https://higgsfield.ai/mcp
- Independent Apache-2.0 project OpenKatana: https://github.com/rk0neki/OpenKatana
- Independent MIT multitrack editor (unrelated implementation): https://github.com/milanofthe/katana

Higgsfield's private source code, weights, proprietary prompts, preset assets and orchestration are **not** available. FFS must use independently developed code and compatible licensed dependencies.

## Product goal

Given a permitted reference video, 1–5 subject/product images, and optional natural-language directions, produce an editable new video that matches the reference's shot structure, cut timing, aspect ratio and motion intent while replacing selected subjects with authorized assets. Never promise pixel-identical outputs.

## Core workflows

1. Upload reference; inspect video metadata, cut boundaries, motion, text and beat positions.
2. Upload images/footage and annotate subjects with stable IDs.
3. Produce a structured, editable shot plan with per-shot timing, constraints, subject IDs and model parameters.
4. Choose a provider per shot; preview estimated costs and require confirmation before billable generation.
5. Generate independently versioned shots; store inputs, provider, seed where available, status, errors and provenance.
6. Assemble shots, titles and audio on multitrack timeline.
7. Accept textual revisions and invalidate only affected shots; use non-generative FFmpeg operations for cuts and timing changes.
8. Export MP4 with explicit dimensions, FPS and audio policy.

## Target architecture

- UI: React/TypeScript timeline, storyboard, assets, prompt editor, render queue.
- Local API: FastAPI, project persistence, FFmpeg and ffprobe.
- Job queue: durable SQLite-based queue initially; worker process for CPU-intensive rendering.
- Asset storage: local content-addressed files, SHA-256, provenance and license metadata.
- Project format: versioned JSON manifest with shots, clips, tracks, revisions, render settings and provider jobs.
- Reference analysis: PySceneDetect/OpenCV, optical flow, beat/onset detection (librosa), optional transcription.
- AI adapters: independent interfaces for text-to-image, image-to-video, video-to-video, motion transfer and inpainting; optional cloud GPU, explicit billing and consent.
- Security: loopback binding, strict upload validation, ffmpeg timeouts, disk quotas, avoid shell=True, SSRF-safe remote asset imports, secret isolation.
- Reliability: idempotent jobs, cancellation, retry budgets, deterministic assembly, migration tests and media fixtures.

## Feature parity matrix

| Feature | Katana documented | FFS status | Priority |
| --- | --- | --- | --- |
| Video reference import | Yes | Basic upload | P0 |
| Shot boundary detection | Yes (behavior) | FFmpeg heuristic | P0 |
| Match cut rhythm/audio | Yes | Not implemented | P0 |
| Subject images (up to 5) | Yes | Not implemented | P0 |
| Structured storyboard | Implicit | Not implemented | P0 |
| Per-shot generative replacement | Yes | Not implemented | P0 |
| Selective regeneration | Yes | Not implemented | P0 |
| Conversational revision | Yes | Not implemented | P1 |
| Community presets | Yes | Not implemented | P2 |
| Local editable timeline | Not established | Single-source clip list | P0 |
| Local export | Delivered result | Basic silent 720p | P0 |
| Transparent cost approval | Yes | Not implemented | P0 |
| Provider portability | Not established | Planned | P1 |
| Offline editing | Not established | Partial | P0 |

## Acceptance criteria for the first real parity milestone

- Upload a permitted 10–30 second reference and five images.
- Persist a versioned shot plan and timeline; reorder shots without altering source files.
- Identify cuts within a documented tolerance against manually annotated fixtures.
- Generate a per-shot provider job plan without charging or uploading until approval.
- Replace a single generated shot and reassemble without rerunning unaffected shots.
- Export H.264/AAC with correct duration and aspect ratio.
- Demonstrate a full test using at least one explicitly supported, licensed model provider.
- Measure cost, generation latency, failure rate, temporal consistency and visual identity consistency.

## Constraints

16 GB RAM, no dedicated server; local editing should work CPU-only. High-quality video generation will typically require remote GPU/API resources and may incur costs. ChatGPT Plus is not an AI video API subscription. Free operation cannot be guaranteed for generation.

## Build order

1. Fix v0.1 media handling and persistence, background rendering, safe file uploads, audio.
2. Reference analyzer: shot graph, optical flow and audio beat map; golden fixture tests.
3. Storyboard + subject library and project schema migrations.
4. Provider abstraction, credit/cost estimate, explicit approval and queue.
5. Generative shot orchestration, versioning and selective regeneration.
6. Prompt-driven revisions, preset system, production UX and packaging.

## Evaluation

Use a benchmark suite with owned/licensed reference clips; compare scene boundary accuracy, shot duration error, cut-to-beat error, character consistency, motion similarity, render stability and cost per finished second. Do not claim Katana-equivalent output without controlled side-by-side tests.
