# M1–M2 — Settlement, resilience, and craft Implementation Plan

> For agentic workers: use the installed subagent-driven-development or executing-plans workflow when available. Execute task-by-task with tests and evidence. Do not require unavailable agent tools.

**Goal:** Make a town grow around player anchors and sustain a real population, seasonal economy, skilled craft, and elite training.

**Architecture:** City geometry and production read the same cohort/resource model. Engine views submit validated commands; local influence caches and aggregate production avoid citizen AI.

**Tech Stack:** Verified Unreal Engine 5/C++, shared engine-independent C++20 simulation, CMake/CTest, Unreal automation, original or licensed content.

**Spec:** `docs/01_BETA_SPEC.md`, `docs/03_SIMULATION_RULES.md`, `docs/05_INTERFACE_AND_CONTENT.md`

## Global constraints

User requirements in `docs/00_PRODUCT_CONTRACT.md` are protected. Exact defaults and limits come from `docs/01_BETA_SPEC.md`. No per-citizen AI, per-soldier Character architecture, personal samurai relationship system, runtime LLM, hidden AI resources, or unverified success claims. Commands below are future wrapper contracts created in M0; their existence is not assumed. New files are proposed paths for a fresh repository; record exact mappings for existing code.

For each task: write the named failing test, run it, implement the behavior, rerun the test and regressions, verify presentation if applicable, update STATUS.md, and commit the coherent change when permitted. Keep the test inputs and expected outputs in the test source, not only in prose. A failed or unavailable gate stays open.

---

## Task 1.1 — Cohort and stock foundations for construction

**Files:** create `domain/Population.h`, `Economy.h`, `Commands.h`; corresponding `Private/sim/Population.cpp`, `Economy.cpp`, `Commands.cpp`; `core/tests/test_population.cpp`, `test_inventory.cpp`.

**Consumes:** World IDs/day. **Produces:** exclusive cohort counts, resource quantities, validated atomic spend/refund commands.

- [ ] Test a 420-person town containing 200 eligible and 220 ineligible/dependent residents: total remains 420 through job assignment and construction staffing.
- [ ] Test a project costing 30 timber with stock 29: failure leaves all stocks and occupancy unchanged. Stock 30 succeeds; one cancellation cannot refund twice.
- [ ] Implement bounded integer stocks and exclusive worker allocation. Add finite migration source and demographic event records without yet making growth mandatory.
- [ ] Bind actual stocks to the settlement header. Zero resources must block building with a reason.

Run `python tools/dev.py core-test --suite population,inventory`; retain exact assertions in the C++ tests.

## Task 1.2 — Roads, parcels, anchors, and infill

**Files:** create `domain/City.h`, `Private/sim/City.cpp`, `core/tests/test_city.cpp`; engine `CityView`, `PlacementController`, `InfluenceOverlay`; author `content/definitions/buildings.json` and `influences.json`.

**Interfaces:** City owns stable road/building/parcel IDs and footprint occupancy; placement returns success or an explicit invalid/access/funds error before mutation. Infill returns funded construction commands, not direct anonymous mesh spawning.

- [ ] Encode T12–T14 with two identical parcels: one accessible, one unconnected. A market and trade demand increase only the eligible parcel's useful commercial score.
- [ ] Implement free-angle main roads over a hidden occupancy raster, frontage parcels, terrain/water validation, public anchors, and ordinary small structures.
- [ ] Add local cached influences, mixed-use selection, private development budgets, gradual construction, and the "why not growing" inspector.
- [ ] Test no overlap, no underwater build, no population from empty housing, repeated-load identity, and persistent pinned structures.
- [ ] Visually check an organic town around two different road layouts. A perfectly identical rectangular city in both is not acceptable.

Run `python tools/dev.py core-test --suite city` and `python tools/dev.py run --scenario quiet_growth`.

## Task 1.3 — Promotion and physical landmark choices

**Files:** extend City/Commands; create `core/tests/test_promotion.cpp`; engine `DistrictPanel`, `ModulePicker`; add module definitions.

**Interfaces:** promotion checks town resident count, administration, infrastructure, and project funding; modules attach to a specific anchor ID and reserve legal footprints.

- [ ] Test promotion at 1,199 versus 1,200 town residents with required administration present. No population, building IDs, or historic roads change when promotion succeeds.
- [ ] Test two alternative market modules with differing footprint, maintenance, storage/access effects, and surrounding demand.
- [ ] Implement gradual district management, stable IDs/names, four soft priorities, and control preservation. Food-risk warnings do not silently prohibit all risky investments.
- [ ] Show the capital's original center still present after automation fills surrounding districts.

**M1 exit:** a playable build can construct and grow a visibly different town, promote it deliberately, and choose an expansion. Seasonal/craft depth remains M2, not a claimed M1 feature.

## Task 2.1 — Seasons, forecast, and biological reserves

**Files:** extend Economy; add `Private/sim/Agriculture.cpp`, `Livestock.cpp`; `core/tests/test_harvest.cpp`, `test_livestock.cpp`; seed/weather/scenario content and food UI.

**Interfaces:** daily economic phases operate on actual land/labor/seed/stores. Forecast returns observed estimate range plus confidence, never hidden final yield.

- [ ] Write T01–T02, T18–T20, T38 for a closed farm fixture. Reducing harvest labor must reduce gathered food; changing camera/UI must not alter weather RNG.
- [ ] Add crop phases, region-correlated weather, narrowing observed forecasts, seed subaccount, spoilage, consumption, and route-dependent import placeholders using real transfer records.
- [ ] Add herd age/breeding/work categories and a slaughter command preview. Decrease exactly the selected stock and future capacity.
- [ ] Bind food days, projected range, and emergency actions. Verify a crisis can be anticipated without exact long-term foreknowledge.

## Task 2.2 — Master smiths, apprentices, tools, and equipment batches

**Files:** create `domain/Crafts.h`, `Private/sim/Crafts.cpp`; `core/tests/test_crafts.cpp`; recipes, skills, equipment content; engine `CraftPanel`.

**Interfaces:** qualified labor + station time + resources + knowledge produce typed, quality-banded equipment batches. Apprenticeship uses explicit mentor capacity and accumulated supervised work.

- [ ] Test one master can supervise only the configured slots; ten extra unsupervised apprentices do not raise advanced output. Zero fuel yields zero completed work.
- [ ] Test volume and quality independently: a larger low-skill operation can produce more basic items but cannot make an elite recipe without qualified supervision.
- [ ] Implement queued production, tools-versus-weapons priority, quality bands, input reservation, and completed equipment storage.
- [ ] Add apprenticeship progress, recruitment/retention incentives, and output recalculation after absence/death. No instant expert replacement.
- [ ] Make the UI identify the actual bottleneck and show changed outputs after a staffing change.

## Task 2.3 — Retainer support and elite readiness

**Files:** extend Population/Crafts, create `content/definitions/training.json`, `core/tests/test_training.cpp`, and military-readiness preview.

**Interfaces:** training consumes eligible people-time, instructors, resources, and supporting capacity; role readiness and equipment remain separate.

- [ ] Test cultural prestige with no equipment/instructors does not create elite troops. Strong equipment with no trained personnel does not create veteran samurai.
- [ ] Implement shallow ordinary progression and deeper elite readiness; record martial standing and social support inputs for M6.
- [ ] Add support costs and training throughput so excellent elites have real replacement constraints.

**M2 exit:** Quiet growth and Risky mobilization previews show real food, labor, craft, and training limits. All economic quantities remain conserved. The city is playable and understandable without opening its detailed ledgers.
