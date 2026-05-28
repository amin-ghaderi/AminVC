## AminVC Architecture

This repository hosts a **unified audiobook platform** as a monorepo, designed for long-term scalability and clear separation of concerns.

## Domain engines

### `narration-engine/` (text → speech)

The narration engine is responsible for converting **text** into **spoken audio**. It encapsulates all TTS concerns such as:

- Text normalization and preprocessing (domain-level)
- Voice selection/conditioning specific to narration (domain-level)
- TTS inference and audio generation (domain-level)

It is treated as a self-contained backend/domain system.

### `speaker-engine/` (voice conversion / speaker consistency)

The speaker engine is responsible for **speaker identity** and **voice conversion** concerns, such as:

- Converting one voice to another (VC)
- Enforcing speaker consistency across segments/chapters
- Speaker embeddings and identity preservation (domain-level)

It is also a self-contained backend/domain system.

## Why `app/` exists

`app/` is the **orchestration + future UI layer**. It exists to compose engines into end-to-end audiobook workflows without coupling engines to each other. `app/` is where we will place:

- UI surfaces (`app/ui`, `app/pages`)
- User-facing orchestration (`app/controllers`)
- End-to-end workflows (`app/pipelines`)
- Coordination services (`app/services`)
- Application state (`app/state`)
- App-level configuration (`app/config`)

## Why engines are isolated

Engines must remain independent so that:

- Each engine can evolve, be swapped, or versioned without rewriting the other.
- We avoid circular dependencies and hidden coupling.
- The orchestration layer (`app/`) can compose capabilities in multiple ways (CLI/UI/API) while keeping domain engines stable.

The dependency direction is intentionally one-way:

```text
app/
  → narration-engine/
  → speaker-engine/
  → pipelines/
  → output (storage/exports)
```

Not:

```text
narration-engine/ → speaker-engine/
speaker-engine/ → narration-engine/
```

## How future pipelines will work

Pipelines will live in `app/pipelines/` and coordinate the flow of data and artifacts:

1. **Input acquisition**: gather text, metadata, and optional reference audio into `storage/input/`.
2. **Narration (TTS)**: call `narration-engine/` to render narration segments into `storage/temp/` (or `storage/cache/` when reusable).
3. **Speaker consistency (VC)**: call `speaker-engine/` to convert/align voice and ensure consistent speaker identity, producing refined audio segments.
4. **Assembly + export**: stitch, mix, and package final audiobook outputs into `storage/exports/` with logs in `storage/logs/`.

`shared/` will host reusable helpers (audio/text/utils/config/logging/constants) used across `app/` and engines, without forcing engines to depend on each other.

