# AI generation provider interface

FFS remains a local-first video editor. AI generation is optional and is **not available yet**.

`app/generation.py` defines a provider-neutral `GenerationProvider` protocol, immutable `GenerationRequest`, and `GenerationResult`. The `DisabledProvider` fails safely rather than silently contacting a service.

Future implementations must:
- require explicit provider configuration and user consent before uploading source video, reference frames or subject images;
- keep API keys on the server and never expose them to browser clients;
- implement job timeouts, cancellation, retries with backoff and idempotency keys;
- validate output media before adding it to the timeline;
- expose cost estimates before a paid generation call;
- isolate provider-specific settings from the project format;
- avoid storing raw user secrets or personally identifying data in logs.

No GPU, model weights or cloud subscription is needed to run the current editor.
