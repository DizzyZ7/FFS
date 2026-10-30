# FrameForge Studio — Katana-class workflow specification

## Product objective
One end-to-end workflow, not isolated editing tools: import reference or source video → add reusable subjects/assets → write a natural-language brief → analyze shots, pacing, audio, typography and transitions → preview a structured plan → recreate/edit → review output → request a change in plain language → regenerate **only affected shots** → export.

This is a product target, not a claim of current functionality. Do not copy proprietary code, presets or brand assets.

## Mode A: Reference Recreate
1. Accept a licensed reference video or original preset and 0–5 subject images.
2. Extract shot boundaries, frame dimensions, timing, audio beats, typography, camera movement and color/style descriptors.
3. Create a versioned, inspectable shot graph. Each shot carries references, generation parameters, audio cues and provenance.
4. Offer an editable preview with estimated costs. Ask for consent before any paid or external provider call.
5. Generate or transform shots through opt-in adapters, with retries, progress, cancellation and deterministic job IDs.
6. Match the reference's shot order, aspect ratio, frame rate and edit rhythm by default.
7. Accept follow-up instructions; compute a dependency diff and invalidate only affected outputs.
8. Export MP4 and retain editable project history.

## Mode B: Voice Auto Edit
1. Record voice or import video/audio.
2. Transcribe offline where possible, align word timestamps, and expose corrections.
3. Detect pauses, repeated takes and filler words; propose non-destructive cuts.
4. Compose motion typography from semantic phrases and word-level timing.
5. Select transitions, reframing and optional B-roll; keep edits reversible.
6. Render audio, animated captions and effects together and export multiple aspect ratios.

## Shared architecture
- Versioned Project Graph: source assets, shots, audio, text overlays, transitions, dependencies, outputs and revisions.
- Analysis: FFmpeg/ffprobe, shot segmentation, beats, OCR, ASR, optional semantic analysis.
- Planner: converts natural-language instructions to validated edit operations; never execute arbitrary code.
- Renderer: local FFmpeg filter graph, cached intermediate assets, preview and full quality.
- Generation: provider adapters and durable worker queue; no secret in browser, explicit consent and cost preview.
- Revision engine: invalidate changed nodes and descendants only; unchanged shots reuse cached outputs.
- Safety: rights confirmation for reference media, project-scoped assets, size limits, content sanitization, auditable revisions.

## Release gates
- **M1:** reference upload, storyboard, subject assignment, editable shot plan, local render.
- **M2:** offline transcription and word-level alignment, caption animation and final video burn-in.
- **M3:** natural-language edit planner and non-destructive revisions.
- **M4:** generation worker, one functioning provider, incremental shot regeneration and cost preview.
- **M5:** reference-motion/style analysis, reusable presets and production-ready export.

## Definition of done for end-to-end parity
A user can submit one reference, up to five subject images and a text brief, get an edited video, request a shot change, see only affected shots rerendered, and export an MP4 — without manually editing the timeline. Voice Auto Edit must also deliver synchronized animated captions from raw speech with no manual transcription.
