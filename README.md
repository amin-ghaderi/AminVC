## AminVC (Monorepo)

AminVC is a modular foundation for a long-term **audiobook creation platform**, built as a monorepo with **independent domain engines** and a separate orchestration layer.

## High-level architecture

- **`narration-engine/`**: text → speech (TTS) domain engine (AminVoice).
- **`speaker-engine/`**: voice conversion / speaker consistency domain engine (SeedVC).
- **`app/`**: orchestration + future UI. Owns pipelines, coordination, and user-facing flows.
- **`shared/`**: reusable cross-project utilities (no engine coupling).
- **`storage/`**: runtime-generated files (inputs, temp, cache, exports, logs).
- **`docs/`**: architecture, decisions, pipeline notes, and migration planning.

Engines are intentionally isolated: the `app/` layer composes them, so neither engine depends on the other.

