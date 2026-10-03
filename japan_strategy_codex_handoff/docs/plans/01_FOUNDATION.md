# M0 — Foundation and scale proof Implementation Plan

> For agentic workers: use the installed subagent-driven-development or executing-plans workflow when available. Execute task-by-task with tests and evidence. Do not require unavailable agent tools.

**Goal:** Create an actually runnable 3D project, a shared testable simulation, and a measured moving-formation laboratory.

**Architecture:** Unreal presents a persistent plain-C++ model. The initial laboratory isolates rendering and formation movement; complete combat benchmarking follows M3/M9.

**Tech Stack:** Verified Unreal Engine 5/C++, shared engine-independent C++20 simulation, CMake/CTest, Unreal automation, original or licensed content.

**Spec:** `docs/02_ARCHITECTURE.md`, `docs/07_TEST_AND_RELEASE_GATES.md`

## Global constraints

User requirements in `docs/00_PRODUCT_CONTRACT.md` are protected. Exact defaults and limits come from `docs/01_BETA_SPEC.md`. No per-citizen AI, per-soldier Character architecture, personal samurai relationship system, runtime LLM, hidden AI resources, or unverified success claims. Commands below are future wrapper contracts created in M0; their existence is not assumed. New files are proposed paths for a fresh repository; record exact mappings for existing code.

For each task: write the named failing test, run it, implement the behavior, rerun the test and regressions, verify presentation if applicable, update STATUS.md, and commit the coherent change when permitted. Keep the test inputs and expected outputs in the test source, not only in prose. A failed or unavailable gate stays open.

---

## Task 0.1 — Audit and build wrapper

**Files:** create `tools/dev.py`, `toolchain.lock.json`, `STATUS.md`; inspect repository instructions, engine project/configuration, and existing build files before modifying them.

**Consumes:** actual host executables and repository state. **Produces:** `doctor`, `core-test`, `editor-test`, `run`, `benchmark`, and `package` wrapper commands with explicit failure semantics.

- [ ] Record existing/uncommitted work; choose an isolated development branch/worktree where available without destructive resets.
- [ ] Add tests that a nonexistent engine path produces a nonzero status and a missing-tool message, and that core tests can run independently of engine discovery.
- [ ] Discover actual engine version/compiler/SDK/OS and write the lock. Do not pin an invented latest release or install a large engine without authorization.
- [ ] Implement the wrapper with Python standard-library subprocess, explicit argument arrays, printed commands, preserved exit status, and configured paths. Never shell-concatenate untrusted paths.
- [ ] Run the audit; mark engine-dependent work BLOCKED when appropriate. An available native build environment should proceed immediately to the next task.

```sh
python tools/dev.py doctor
```

Expected: a real environment report and explicit status for each build target. A missing Unreal executable must not be reported as an installed editor.

## Task 0.2 — Portable shared core and first red/green test

**Files:** create `game/Source/DomainCore/Public/domain/Types.h`, `World.h`, `Content.h`; `game/Source/DomainCore/Private/sim/World.cpp`; `core/CMakeLists.txt`; `core/tests/test_clock.cpp`; module bootstrap/build file under DomainCore.

**Interfaces:** `World` initially exposes `Day day = 0` and `uint64_t seed`; `Content` holds configuration; `AdvanceOneDay(World&, const Content&)` advances exactly one integer day. It must not depend on any Unreal type. Extend World later without changing this clock contract.

- [ ] Write this initial test before implementing `AdvanceOneDay`; configure CTest to execute it and retain its initial failure.

```cpp
#include "domain/World.h"
#include "domain/Content.h"
#include <iostream>
int main() {
    domain::World world{};
    domain::Content content{};
    for (int i = 0; i < 360; ++i) domain::AdvanceOneDay(world, content);
    if (world.day != 360) {
        std::cerr << "expected 360 days, got " << world.day << '\n';
        return 1;
    }
    return 0;
}
```

- [ ] Implement day advancement and stable ID allocation; add seed-isolated RNG state with serialization-ready counters. Rendering calls cannot consume weather/combat RNG.
- [ ] Test 360 one-day calls versus grouped batches totaling 360; duplicate-ID prevention; independent stream changes; zero/negative command validation.
- [ ] Build the same source files through CMake and the Unreal module. Exclude only the Unreal module bootstrap from CMake.

```sh
cmake -S core -B build/core -DCMAKE_BUILD_TYPE=Debug
cmake --build build/core --config Debug
ctest --test-dir build/core -C Debug --output-on-failure
```

Expected: actual compiled tests pass in both the wrapper and direct invocation. Do not add a parallel Python implementation to make tests easier.

## Task 0.3 — Runnable scene and strategy controls

**Files:** create `game/Source/DomainGame/DomainGame.Build.cs`, `DomainRuntimeSubsystem.h/.cpp`, `StrategyCameraPawn.h/.cpp`, `DomainPlayerController.h/.cpp`, and a verified initial map under `game/Content/Domain/Maps/`; adapt project settings to the installed engine.

**Consumes:** shared World clock and IDs. **Produces:** persistent runtime owner, camera/selectable objects, pause/speed control, on-screen model values.

- [ ] Add engine tests for starting a world, selecting a known object ID, pausing, and changing speed without changing simulated results.
- [ ] Implement camera pan/rotate/zoom and selection with a simple original manor/terrain layout. The displayed population/stock readout may be a fixed starting fixture at M0, clearly marked; no claim that economy is complete.
- [ ] Create/import real engine assets through a verified process. Open and run the scene. Capture a screenshot and input smoke test.
- [ ] Package a minimal runnable build if tools allow; otherwise record editor-only verification explicitly.

```sh
python tools/dev.py editor-test --suite foundation
python tools/dev.py run --scenario foundation
```

## Task 0.4 — Formation representation benchmark before art expansion

**Files:** create `FormationView.h/.cpp`, `SoldierRenderAdapter.h/.cpp` in DomainGame; `domain/Battle.h` initial formation/slot types; `core/tests/test_slots.cpp`; `content/scenarios/scale_lab.json`.

**Consumes:** stable formation/service IDs and poses. **Produces:** batched moving soldier representation and selectable individual formations with origin fixture labels.

- [ ] Test unique membership, slot assignment, formation drag target positions, and no overlap in a commanded line of ten formations.
- [ ] Implement 1,000 then 8,000 then 20,000 represented soldiers with 100-person formations. Log actual live formation/instance counts and controller counts. No one-Character-per-soldier fallback.
- [ ] Pan/zoom, give group orders, turn formations, cross a narrow simple passage, and change selection during measurement. Evaluate instancing/near-camera animation costs; document backend choice.
- [ ] Store frame-time/memory evidence on actual hardware. Label this movement/representation-only; it is not the final combat benchmark.

```sh
python tools/dev.py benchmark --scenario scale_lab --soldiers 8000 --seconds 120
python tools/dev.py benchmark --scenario scale_lab --soldiers 20000 --seconds 120
```

**M0 exit:** shared core compiles, scene launches, input works, real counts match, benchmark report exists, bottlenecks/next changes are documented. If no graphical execution is available, M0 remains partially blocked, though core work can be verified.
