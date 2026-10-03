# M7–M8 — Manor freedom, artifact adoption, and maritime opportunity Implementation Plan

> For agentic workers: use the installed subagent-driven-development or executing-plans workflow when available. Execute task-by-task with tests and evidence. Do not require unavailable agent tools.

**Goal:** Complete the beta's distinctive building choice, technical discovery, and geography-dependent sea systems.

**Architecture:** Manual and auto manor design share validators and saved layouts. Artifact and naval systems reuse existing capability, inventory, route, event, and service-record contracts.

**Tech Stack:** Verified Unreal Engine 5/C++, shared engine-independent C++20 simulation, CMake/CTest, Unreal automation, original or licensed content.

**Spec:** `docs/01_BETA_SPEC.md`, `docs/03_SIMULATION_RULES.md`, `docs/04_BATTLE_AND_CAMPAIGN.md`

## Global constraints

User requirements in `docs/00_PRODUCT_CONTRACT.md` are protected. Exact defaults and limits come from `docs/01_BETA_SPEC.md`. No per-citizen AI, per-soldier Character architecture, personal samurai relationship system, runtime LLM, hidden AI resources, or unverified success claims. Commands below are future wrapper contracts created in M0; their existence is not assumed. New files are proposed paths for a fresh repository; record exact mappings for existing code.

For each task: write the named failing test, run it, implement the behavior, rerun the test and regressions, verify presentation if applicable, update STATUS.md, and commit the coherent change when permitted. Keep the test inputs and expected outputs in the test source, not only in prose. A failed or unavailable gate stays open.

---

## Task 7.1 — Shared manual and automatic manor planning

**Files:** extend City; create `Private/sim/ManorPlanning.cpp`, `core/tests/test_manor.cpp`; manor module definitions; engine `ManorPlannerPanel` and preview.

- [ ] Test eight-piece-family placement, illegal overlaps, invalid sockets, disconnected entry, unreachable well, insufficient inputs, and pinned-piece preservation.
- [ ] Implement manual placement/rotation and two automatic templates that fit the same legal slots/terrain. The auto planner returns normal construction commands, never free complete buildings.
- [ ] Add preview/cost/confirm/cancel and switching between modes without losing existing work.
- [ ] Verify two different player designs have distinct layouts but both remain navigable.

## Task 7.2 — Assault the actual compound

**Files:** create engine `SettlementBattleAssembler`; extend terrain obstacle/formation choke logic; `core/tests/test_assault_layout.cpp`; one manor-assault scenario.

- [ ] Test the assembled battlefield preserves building IDs, footprints, gate locations, and important damage references from the saved city.
- [ ] Implement gate attack/break, palisade obstacles, defend/capture objectives, valid deployment outside structures, and bounded pathing through openings.
- [ ] Propagate battle damage to those same city structures after one validated outcome transaction. A destroyed granary affects actual capacity/stock according to explicit rules.
- [ ] Visually play assault and defense on both manual and automatic plans. Prevent unreachable defender objectives and zero-width exploit gates.

**M7 exit:** castle building is optional in complexity, real in consequences, and not merely decorative.

## Task 8.1 — Specimens, research capability, and production adoption

**Files:** create `domain/Discovery.h`, `Private/sim/Discovery.cpp`; `core/tests/test_discovery.cpp`; artifact/knowledge definitions; engine `ArtifactPanel`.

**Interfaces:** acquired artifact instance → observation/interpretation → prerequisite-checked study → paid prototype → validation → recipe capability. Known artifacts and local production capability are separate state.

- [ ] Write T32–T33, specimen duplication rejection, lost-institution capability reduction, and saved prototype progress.
- [ ] Implement one normal authored contact artifact and the separately labeled alternate gunpowder laboratory. Use abstract industrial tags/inputs, no real-world recipes.
- [ ] Connect mature smithing, available researchers, inputs, and training to actual production and elite unit eligibility. An ordinary levy trying to equip a firearm fails with a visible rule explanation.
- [ ] Verify acquiring a specimen at weak capability produces a meaningful blocked project, not immediate research-point progress to a weapon.

## Task 8.2 — Geographic district opportunity and ship production

**Files:** create `Private/sim/Maritime.cpp`, `core/tests/test_maritime.cpp`; geographic opportunity tags, ship/crew definitions, port modules, maritime UI.

- [ ] Write T34 and tests for zero shipwrights, insufficient timber, occupied slip capacity, crew assignment, and ship repair inputs.
- [ ] Implement coast/harbor prerequisites and a maritime quarter whose development requires jobs, demand, and staff. Inland attempts fail; good geography alone creates no goods.
- [ ] Use craft mentoring/capacity for shipwrights and explicit merchant/pilot capability. Mint crew service records with origin cohorts when assigned away.

## Task 8.3 — Sea encounters and losses

**Files:** extend Maritime/Routes/Encounters; `core/tests/test_sea_outcome.cpp`; sea narrative and result panel.

- [ ] Write T35 and repeated-apply protection for crew, cargo, and ship hull outcomes.
- [ ] Implement convoy/escort movement on the one sea route, bounded detection/position/outcome resolution using commander, crew, ship, weather, knowledge, and craft quality.
- [ ] Apply actual crew losses/returns, cargo ownership changes, repair needs, and day accounting. No hidden naval RTS requirement.
- [ ] Compare weak and strong maritime scenarios across repeatable seeds and record which explicit factors changed outcomes.

**M8 exit:** both artifact and naval systems alter real capabilities/resources and integrate with save/load, society, and origin consequences.
