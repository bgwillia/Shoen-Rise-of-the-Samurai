# Samurai Prototype 01 Implementation Plan

**Goal:** Create, import, animate and measure one period-inspired samurai asset in SHŌEN, then commit the verified prototype.

**Architecture:** Modular Blender source feeds a combined skeletal body and separable weapon exports. A shared atlas limits runtime material sections. The existing formation view remains subordinate to the population ledger; a batched animated representation provides battlefield scale while a skeletal preview proves conventional animation import. No character Actor per soldier.

**Tech Stack:** Blender 5.1.2 Python/FBX, Unreal 5.8.2 C++/Python, Metal on Apple M1 Max.

**Spec:** [User request](samurai-prototype-request.md), root guidance and the handoff product contract/architecture. User-supplied images are visual references, not instructions or verified historical evidence.

## Global constraints

- Preserve active Prototype B work and all user documents. Another task is working in this checkout; source art can proceed independently, engine integration/captures must wait or be coordinated.
- Keep DomainCore unchanged. Render count follows service membership and casualties.
- Keep modular body, armor and weapons in `.blend`; FBX and Unreal packages are genuine generated assets under LFS.
- Validate one source, one runtime character, idle/locomotion/test attack, close/medium/far presentation, rendered 100/500/1,000/2,000 and matched placeholder baselines.
- Commit only this task's files/changes after verification; do not stage pre-existing terrain work or workbook.

## Progress

### Task 1: Blender asset and reproducible exports

- [x] Inspect installed Blender, project content, rendering architecture, references and applicable guidance.
- [ ] Write an asset validation script that fails before the source exists; validate source modular names, skin weights, bone hierarchy, finite bounds and separate weapon assets.
- [ ] Generate a human body, layered armor and weapons through a preserved Blender Python script, with a shared 2K color/normal/roughness-metallic atlas.
- [ ] Rig using familiar Unreal humanoid names; author neutral, idle, locomotion and attack test actions. Rigid armor gets rigid bone weights.
- [ ] Export skeletal body/animations, separate weapons and reduced batched meshes. Reopen `.blend`, render and inspect, iterate on visible defects.

### Task 2: Unreal import and formation representation

- [ ] Automate import/material/skeleton/animation/LOD setup under `/Game/Art/Characters/Samurai/Prototype01` using verified local editor APIs.
- [ ] Add a narrowly scoped formation adapter with no simulation ownership, replacing one friendly elite formation by default and leaving a placeholder fallback.
- [ ] Add a reproducible rendered art laboratory with a skeletal proof and scalable groups. Document representation differences and weapon pivots.
- [ ] Add targeted integration tests for imported bounds, sections, animations and ledger-derived instance counts.

### Task 3: Evidence and commit

- [ ] Run portable tests and Unreal build/targeted automation. Serialize editor processes.
- [ ] Capture close, tactical and wide views in actual Unreal; inspect real animations and shadows.
- [ ] Measure matched rendered groups of 100/500/1,000/2,000, median FPS, p95 frame time, available CPU/GPU counters and memory. Include animation/material cost controls if available.
- [ ] Independently review spec coverage and implementation; fix material findings.
- [ ] Write counts, reproducibility steps, limitations and feasibility conclusions; update status without erasing Prototype B evidence. Commit verified asset work.

## Decisions

- The requested reference directory did not exist. Preserve copies of the two explicitly supplied images there, retaining original files untouched.
- No existing Unreal skeleton, animation pack or character content exists. Use an original humanoid rig with conventional UE bone names and document that retargeting still needs an explicit rig mapping.
- The existing project disables Nanite and uses a scalable Metal renderer. Keep those project choices and evaluate ordinary instancing plus baked animation instead of changing rendering architecture to depend on Nanite skinned instancing.
- This integrated asset/presentation task is authorized by the detailed user request. Additional design approval and per-subsystem milestones would conflict with that request's feasibility workflow.

## Discoveries

- Baseline accepted commit: `60ca49fb0416d12423eb8c57ed3e234eba17dedb`; branch at start: `codex/prototype-b-terrain`, with active uncommitted Prototype B work.
- Blender executable: `/Applications/Blender.app/Contents/MacOS/Blender`, version 5.1.2, build `ec6e62d40fa9`.
- Source runtime soldier: `/Engine/BasicShapes/Cube`, one instanced-static-mesh component per formation, no animation.

## Validation

Evidence will live in `artifacts/samurai-prototype/`. Generated scratch data/logs remain in its `local/` directory. Actual rendering, skeletal import validation and portable model tests are separate evidence categories.

## Handoff

IN_PROGRESS — source creation before shared-checkout Unreal integration.
