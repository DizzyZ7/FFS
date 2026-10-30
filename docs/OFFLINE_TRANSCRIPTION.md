# Offline speech transcription

Optional installation: `pip install faster-whisper`.

Once a video has been uploaded, call `POST /api/projects/{project_id}/transcription?model=tiny` to get word timestamps. Supported models: `tiny`, `base`, `small`. CPU int8 is the default, for machines without a dedicated GPU.

First use may download model weights. This requires internet and disk space; for offline deployment, pre-cache the model in the runtime's model cache. No video or audio is sent to an external inference API by this implementation.

Response: `{"language":"en","model":"tiny","words":[{"start":0.1,"end":0.4,"text":"Hello"}]}`.

The model is loaded lazily and cached; transcription is synchronous and can take time. Future work: background worker, progress, user transcript correction, alignment QA, caption render integration and speech-edit preview. No claim of automatic finished-video generation is made at this stage.
