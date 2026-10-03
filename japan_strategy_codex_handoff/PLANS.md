# Execution plans and continuity

The documents in `docs/plans/` are implementation blueprints. They name future files and command contracts; those files and wrappers do not already exist just because this handoff names them. Codex must create and test them. Adapt paths only after inspecting an existing repository and record the adaptation.

## Authority

The user's explicit requirements in `docs/00_PRODUCT_CONTRACT.md` take precedence over recommended defaults. The beta scope defines what must be built now. The roadmap defines later work and extension boundaries, not permission to implement every system immediately. Historical notes identify intentional fiction; they do not override the user's desired alternate history.

## Workflow per task

Read the active subsystem spec and plan. State the observable deliverable. Write a failing test of the specified behavior, run it and retain its failure, implement the minimal behavior, then run the test and relevant regression suite. Check visuals in the actual engine for any camera, placement, UI, animation, or combat-visibility change. Capture evidence. Commit the coherent change if source control is available and the working tree permits it. Never overwrite unrelated uncommitted changes.

For tasks larger than the next testable change, create a local executable plan under `docs/execution/` with the actual paths and commands discovered during inspection. It must contain Goal, Architecture, Spec, Progress, Decisions, Discoveries, Validation, and Handoff. Expand unresolved implementation details into explicit testable steps before writing that subsystem, not into a speculative giant framework.

## Progress and evidence

Create `STATUS.md` using the supplied template. Every task is NOT_STARTED, IN_PROGRESS, BLOCKED, or VERIFIED. VERIFIED requires evidence rather than a percentage. Include engine version, OS, CPU/GPU/RAM, source revision, content version, and whether the result is editor-only or packaged. Preserve benchmark logs and report paths under `artifacts/`; do not put machine-specific secrets into reports.

An implementation session ends with the current deliverable, actual validation, outstanding failures, and the precise next task. Continue the existing milestone on resumption. Do not restart the architecture because context was lost.

## Commands to implement in M0

`python tools/dev.py doctor`, `core-test`, `editor-test`, `run`, `benchmark`, and `package` are wrapper contracts. The wrapper must discover/configure the actual engine paths, print commands before executing, propagate failures, and report unavailable dependencies honestly. It must not return success for an operation that was skipped. `doctor` writes the toolchain lock and creates no game-content assumptions.

Portable tests must also work directly with CMake/CTest. Engine build/test/package commands are platform-specific; verify them against the installed engine and record the exact invocation. Never claim an Unreal command from an example is known to work before running it.

## Review gates

After M0, inspect whether the representation and formation control actually support the target before expanding content. After M4, inspect whether battle losses really damage production and preserve population accounting. After M6, inspect whether AI information and coalition behavior are fair. After M9, inspect the packaged game against every beta release gate.

Use independent review when available, with feature-spec conformance checked separately from code quality. Parallel workers may handle isolated render assets, UI, or tests after the owning simulation interfaces are agreed. Do not let multiple workers concurrently rewrite population ownership, save formats, or the battle-result transaction.

## Blockers

Missing engine/editor access does not authorize a browser replacement. Missing paid assets does not block original placeholder art. Missing historical certainty does not authorize invented history; label the authored scenario appropriately. Missing measured performance does not authorize claiming the final scale. A blocked task stays open while independent verifiable work continues.
