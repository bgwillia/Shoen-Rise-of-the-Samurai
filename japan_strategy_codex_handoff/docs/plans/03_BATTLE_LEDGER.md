# M3–M4 — Tactical fighting and exact aftermath Implementation Plan

> For agentic workers: use the installed subagent-driven-development or executing-plans workflow when available. Execute task-by-task with tests and evidence. Do not require unavailable agent tools.

**Goal:** Deliver real formation battles and connect actual individual service outcomes back to home districts without duplication.

**Architecture:** Formation-level movement/combat uses the service registry as authoritative membership. Recruitment and battle outcome application are atomic model operations; views never invent outcomes.

**Tech Stack:** Verified Unreal Engine 5/C++, shared engine-independent C++20 simulation, CMake/CTest, Unreal automation, original or licensed content.

**Spec:** `docs/02_ARCHITECTURE.md`, `docs/03_SIMULATION_RULES.md`, `docs/04_BATTLE_AND_CAMPAIGN.md`

## Global constraints

User requirements in `docs/00_PRODUCT_CONTRACT.md` are protected. Exact defaults and limits come from `docs/01_BETA_SPEC.md`. No per-citizen AI, per-soldier Character architecture, personal samurai relationship system, runtime LLM, hidden AI resources, or unverified success claims. Commands below are future wrapper contracts created in M0; their existence is not assumed. New files are proposed paths for a fresh repository; record exact mappings for existing code.

For each task: write the named failing test, run it, implement the behavior, rerun the test and regressions, verify presentation if applicable, update STATUS.md, and commit the coherent change when permitted. Keep the test inputs and expected outputs in the test source, not only in prose. A failed or unavailable gate stays open.

---

## Task 3.1 — Movement, contact, and command groups

**Files:** extend `domain/Battle.h`; create `Private/sim/BattleMovement.cpp`, `BattleCommands.cpp`; `core/tests/test_formation.cpp`; engine `BattleInput`, `ArmyBrowser`, and formation previews.

**Interfaces:** `StepBattle` advances one 20 Hz step from explicit commands. Formation controller outputs legal pose/frontage/slot targets, not individual pathfinding requests.

- [ ] Test individual and 10-formation line orders, facing changes, waypoint queue, and slot preservation through a turn.
- [ ] Add formation-level navigation, local neighbor avoidance, choke-width transitions, and bounded stuck recovery. Fixed inaccessible destinations reject clearly.
- [ ] Implement individual selection, many-unit grouping, drag frontage, and unit filters. No 20-unit hard cap.
- [ ] Verify control of at least 80 formations and passage through a bridge fixture. Retain failed navigation cases as regression scenarios.

## Task 3.2 — Combat, elite roles, and enemy behavior

**Files:** create `Private/sim/BattleCombat.cpp`, `BattleMorale.cpp`, `BattleAI.cpp`; `core/tests/test_combat.cpp`, `test_morale.cpp`; troop/weapon content and visible state animation.

**Interfaces:** contact and volleys select eligible actual service IDs; no city mutation occurs during individual hit processing. Battle AI receives a visibility-filtered view.

- [ ] Test rear attacks, terrain/cover, ammunition depletion, fatigue, no melee kills in untouched distant reserves, and casualty bounds.
- [ ] Implement five roles, armor/skill/weapon distinctions, charge resolution, melee frontage limits, ranged attack, cohesion, morale, and routing.
- [ ] Test supported elite samurai outperform ordinary troops in their intended roles but lose effectiveness when flanked/exhausted/outnumbered. Record scenario results, not a vague "balanced" assertion.
- [ ] Implement enemy line, missiles, reserve, and flanking logic without hidden-unit knowledge.
- [ ] Verify readable attacks, movement, routing, and death states in the rendered game. Cosmetic missiles may be batched; actual shots/ammunition cannot be fictitious.

## Task 3.3 — Battle completion and performance check

**Files:** create `Private/sim/BattleOutcome.cpp`; `core/tests/test_battle_outcome.cpp`; engine battle result view; scale/contact scenarios.

- [ ] Test T11 and a full battle with 100 service IDs: every ID has one disposition; withdrawal survivors remain alive.
- [ ] Implement objective victory, loss of coherent resistance, withdrawal regions, bounded capture/missing rules, and battle completion.
- [ ] Upgrade the scale laboratory to expose an explicit benchmark mode. Re-run 8,000-soldier and 20,000-soldier fixtures with real combat and active controls; record `mode=combat`, live unit counts, and separate stress results.

**M3 exit:** battle laboratory is genuinely playable with AI and outcomes. This is still not an integrated campaign until M4.

## Task 4.1 — Muster and deploy real workers

**Files:** create `domain/Recruitment.h`, `Private/sim/Recruitment.cpp`; `core/tests/test_recruitment.cpp`; engine `MusterPanel`; `core/tests/fixtures/ServiceFixture.h`.

**Fixture contract:** create a closed town with 420 living people: 120 eligible agricultural workers, 40 eligible smith apprentices, 40 eligible retainers, and 220 ineligible/dependent residents. Muster 60/20/20 respectively. No masters are implicitly present. Starting home availability is 200, then 100. All 100 service IDs preserve exact origins.

- [ ] Write T03–T05 and insufficient-equipment rejection before recruitment implementation.
- [ ] Implement protected-specialist selection, explicit override, equipment reservation, muster delay, army provision storage, cancellation, and travel/return status.
- [ ] The tactical army is built from the same roster; inspecting a soldier shows the fixture's actual origin.

## Task 4.2 — Apply exact casualties and recovery

**Files:** extend Recruitment/Population; create `Private/sim/ApplyBattleOutcome.cpp`; `core/tests/test_aftermath.cpp`; engine `AftermathPanel`.

**Outcome fixture:** agriculture: 6 dead, 9 wounded, 3 captive, 42 healthy; smith apprentices: 2 dead, 3 wounded, 1 captive, 14 healthy; retainers: 2 dead, 3 wounded, 1 captive, 14 healthy. Totals: 10/15/5/70 = 100.

- [ ] Write T06–T10 with exact cohort and global totals. The living population becomes 410; home availability stays 100 immediately after battle, then 170 after 70 healthy return. Recovering five wounded makes 175 available. The other living absent/recovering people remain accounted for.
- [ ] Implement transactional result validation/apply keyed by battle ID and starting world revision. Reapply returns AlreadyApplied with no mutation or repeated day increment.
- [ ] Add actual smith output recalculation and contextual warrior/ally loss events for the politics system.
- [ ] Verify the battle report links to the affected districts and produces no fabricated losses in untouched professions.

## Task 4.3 — Snapshots, level transitions, and campaign loop

**Files:** create `domain/SaveCodec.h`, `Private/sim/SaveCodec.cpp`; `core/tests/test_save.cpp`; engine `DomainSaveAdapter`, `SceneTransitionController`; game save/checkpoint actions.

- [ ] Write save roundtrip, corruption rejection, duplicate-result protection, and same-seed continuation tests before building the integration.
- [ ] Serialize World plus active encounter/tactical state at a stable boundary, with lengths/version/content/RNG validation and backup handling.
- [ ] Run city → muster → battle → outcome → district → save → load. Repeat the result screen and reload during/after battle without duplicating anyone.
- [ ] Add pre-battle autosave and explicit tactical checkpoint restore.

Run `python tools/dev.py core-test --suite recruitment,aftermath,save`, `editor-test --suite city_battle_loop`, then play Costly victory and Defeated but recoverable.

**M4 exit:** the defining city/war feedback loop is real, recorded, and recoverable. No hidden generic manpower pool can substitute for the service ledger.
