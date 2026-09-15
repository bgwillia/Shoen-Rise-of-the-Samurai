# Independent review

The first placement slice received separate core, integration and final acceptance reviews.

- Core review identified a persisted-terrain validation gap: a checksum-valid building could be moved onto steep ground while preserving its center height. Retained failing tests reproduce this. Frozen original per-building slope/height tolerances and whole-footprint terrain checks now reject those records while keeping saves valid after stricter catalog tuning. Final core/placement sanitizer results are recorded separately.
- Unreal integration review checked replacement-world generations, stale/canceled input, same-frame duplicate confirmation, file restoration, and passive view recreation. No remaining important lifecycle defect was identified.
- Renderer review traced mesh-description ownership, winding, Canvas batching/depth state, and explicit Metal draw parameters. No source evidence established a leaked instance count/base instance/vertex offset. Engine-supported binding-reset and serialization diagnostics did not eliminate the reproduced glyph corruption; no engine/global CVar workaround remains.
- Final read-only user-spec audit found no additional material gap beyond then-pending HUD fallback rendering, affected regressions and commit. It checked core, Unreal, v1/v2 policy, actual manual loop, scope exclusions, placeholders and performance limits. It explicitly preserved the distinction between tool-driven visible-game actions and absent new human direct-HUD-click/continuous-pointer attestation.

- A final follow-up restored the original Canvas HUD and ISM presentation after the Slate and static-batch hypotheses lacked support. A scoped source/whitespace check confirmed no experimental renderer symbols remained. The unresolved text symptom is recorded as a limitation, not a fix.

Reviews are supporting evidence. The root task independently runs final commands and inspects the rendered game; review alone is not test or rendering evidence.
