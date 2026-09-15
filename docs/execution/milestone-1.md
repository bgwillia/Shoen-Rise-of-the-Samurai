# SHŌEN Milestone 1 implementation plan

**Goal:** Build the user's first technical milestone only: a playable Unreal foundation, exact population accounting, fixed campaign days, save/load, and an instanced formation laboratory.

**Architecture:** One persistent Unreal game-instance subsystem owns an engine-independent C++20 `domain::World`. Civilian cohorts contain exclusive home counts. Mobilization creates stable service records; formations reference those records. Rendering never owns population. CMake and Unreal compile the same simulation sources.

**Spec:** User's attached Milestone 1 request, then `japan_strategy_codex_handoff/docs/00_PRODUCT_CONTRACT.md`, `01_BETA_SPEC.md`, `02_ARCHITECTURE.md`, `03_SIMULATION_RULES.md`, and `docs/plans/01_FOUNDATION.md`. This scope includes early ledger/save proofs, not the handoff's settlement-building M1 or full M4 gameplay.

## Audit

- Initial commit `39c1c0c`, branch `main`, GitHub origin `bgwillia/Shoen-Rise-of-the-Samurai`; only README tracked.
- User-provided handoff directory, ZIP and asset spreadsheet are untracked; preserve them.
- No existing Unreal project, source, plugins, maps, builds, or tests.
- Installed engine `/Users/Shared/Epic Games/UE_5.8`, version 5.8.2, changelist 56702186.
- macOS 26.6.2, Apple M1 Max, 10 CPU / 32 GPU cores, 32 GB memory; Xcode selected, Apple Clang 21.0.0.
- CMake and Git LFS unavailable on PATH. `xcrun metal --version` reports missing Metal Toolchain. Resolve prerequisites where permitted; retain exact blockers.

## Global constraints

- Stop after this milestone; no full settlement economy, combat, diplomacy, campaign routes, or final art.
- Ordinary lab formations contain 100 people; presets 1,000 / 4,000 / 8,000 / 20,000. Last preset is measurement only.
- Start year 1180, 360-day simulation calendar, one day per three seconds at 1×. Pause / 1 / 3 / 5 / 10 alter day count processed, never day size.
- Exact service origin includes settlement, district, cohort, occupation, skill and estate. Dead is separate from wounded; returned records cannot be reused as active soldiers.
- Outcome and demobilization transactions validate before mutation. Saves are versioned, bounded, checked, and validated before replacing live state.
- No one-Actor-per-soldier representation. Primitive instanced geometry is explicitly temporary.
- Never label skipped build, launch, rendering or benchmark checks as passing.

## Tasks and progress

### 1. Repository and executable tools

Files: `.gitignore`, `.gitattributes`, `tools/dev.py`, `tools/tests/test_dev.py`, `toolchain.lock.json`.

- [x] Configure Unreal generated-file exclusions and LFS patterns without staging user documents.
- [x] Test missing engine failures and engine-independent core execution, retain initial failure evidence.
- [x] Implement `doctor`, `core-test`, `build`, `create-map`, `editor-test`, `run`, `benchmark`, `package` using argument arrays and propagated failures.
- [x] Verify actual engine/compiler/build prerequisites; record machine data without hardware identifiers.

### 2. Authoritative portable simulation

Files: `game/Source/DomainCore/Public/domain/`, `game/Source/DomainCore/Private/sim/`, `core/CMakeLists.txt`, `core/tests/`.

- [x] Write and run failing tests for the nine user invariants plus invalid commands, stable IDs, corrupted saves and deterministic continuation.
- [x] Define settlement/district/cohort, occupations, resources, general attributes, services and formation membership.
- [x] Implement fixed-day clock, transactional mobilization, exact per-service result application, demobilization and population summaries.
- [x] Implement versioned snapshot codec preserving clock remainder, resources, IDs, origins and applied transaction IDs.
- [x] Test the requested 200 → 100/100 → 165 available / 15 recovering / 20 dead sequence.
- [x] Run CMake/CTest on these same sources; store output under `artifacts/`.

### 3. Unreal scene and presentation

Files: `game/Shoen.uproject`, `game/Config/`, `game/Source/Shoen*.Target.cs`, `game/Source/DomainCore/DomainCore.Build.cs`, `game/Source/Shoen/`, `tools/create_foundation.py`, real engine-generated map.

- [x] Add C++ modules and engine automation tests; build against installed UE 5.8.2.
- [x] Persistent subsystem owns the core world and snapshot file operations.
- [x] Generate a real minimal map through the installed editor Python API; C++ game mode creates primitive ground, markers and instanced formations.
- [x] Implement smooth WASD pan, middle-drag rotation, wheel zoom and zoom-scaled speed.
- [x] Implement individual/box/additive selection, right-click move, right-drag facing and Ctrl-number groups.
- [x] Display simulation date/speed, counts, selected origins and actionable errors; expose speed, presets, scripted accounting stages and save/load.
- [x] Keep rendered instance membership synchronized to authoritative active service records.

### 4. Verification and handoff

Files: `STATUS.md`, `artifacts/`, `README.md`, `content/provenance/README.md`.

- [x] Run portable regression suite and Unreal editor build/automation.
- [x] Launch rendered scene; verify keyboard accounting/save proof and rendered benchmark camera/formation presentation; capture evidence.
- [ ] Complete physical mouse/held-key acceptance; cached Mac cursor routing remains under investigation (see STATUS.md).
- [x] Run actual moving formation benchmarks and retain frame/memory data. If graphics is blocked, report no rendering measurements.
- [x] Review spec coverage separately from code quality; resolve defects.
- [x] Update STATUS with exact commands, results, placeholders, remaining issues and one next task.

## Decisions

- Preserve the handoff at its discovered directory; do not rename it to `design-handoff`.
- Use `Shoen` as Unreal project/presentation module name; retain `DomainCore` and `domain` namespace to match the supplied architecture.
- Use one instanced-mesh component per formation so rigid movement changes one component transform, with no per-frame per-soldier Actor work.
- Lab fixtures create explicitly finite civilian source cohorts and mobilize them through the real ledger. Preset reset is a labeled new test scenario, not campaign recruitment.
- Implement requested scripted outcomes only as a labeled accounting proof; no claim of tactical combat.
- Work directly in this newly initialized repository on a feature branch so untracked source documents remain available. No existing runtime systems require a separate checkout.
- The attached request and CODEX_START_HERE authorize implementation, overriding additional design-approval ceremony. The supplied foundation plan authorizes isolated implementation agents and independent review. One worker owns the entire population/save model; other work is tooling and Unreal presentation.

## Discoveries

Resolved CMake, Git LFS and the separate Xcode Metal Toolchain prerequisite. Built UE 5.8.2 and launched Metal SM5. Repaired native input classes, inherited debug-key collisions, and the noisy default cube material. A stale Mac cursor/input-delivery issue remains open after the user reported an unresponsive preset button. No speculative coordinate scaling or engine patch was applied.

## Validation

Commands: `python3 tools/dev.py doctor`, `python3 tools/dev.py core-test`, `python3 tools/dev.py build`, `python3 tools/dev.py create-map`, `python3 tools/dev.py editor-test --suite foundation`, `python3 tools/dev.py run --scenario foundation`, and `python3 tools/dev.py benchmark --soldiers 8000 --seconds 120` (then 20,000 stress).

## Handoff

The remaining unchecked item is physical input acceptance. Tests and executable output determine completion; see STATUS.md for actual results and scope limits. Do not advance to the next game milestone automatically.
