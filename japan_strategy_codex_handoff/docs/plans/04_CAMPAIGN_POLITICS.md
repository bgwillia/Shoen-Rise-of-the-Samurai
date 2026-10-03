# M5–M6 — Routes, intelligence, institutions, and coalitions Implementation Plan

> For agentic workers: use the installed subagent-driven-development or executing-plans workflow when available. Execute task-by-task with tests and evidence. Do not require unavailable agent tools.

**Goal:** Turn the integrated city and battle systems into a playable regional campaign with fair AI and social consequences.

**Architecture:** A node/edge map generates reachable encounter snapshots. Faction observation views protect hidden information; event-based politics uses real aid, losses, and occupation history.

**Tech Stack:** Verified Unreal Engine 5/C++, shared engine-independent C++20 simulation, CMake/CTest, Unreal automation, original or licensed content.

**Spec:** `docs/04_BATTLE_AND_CAMPAIGN.md`, `docs/03_SIMULATION_RULES.md`, `docs/01_BETA_SPEC.md`

## Global constraints

User requirements in `docs/00_PRODUCT_CONTRACT.md` are protected. Exact defaults and limits come from `docs/01_BETA_SPEC.md`. No per-citizen AI, per-soldier Character architecture, personal samurai relationship system, runtime LLM, hidden AI resources, or unverified success claims. Commands below are future wrapper contracts created in M0; their existence is not assumed. New files are proposed paths for a fresh repository; record exact mappings for existing code.

For each task: write the named failing test, run it, implement the behavior, rerun the test and regressions, verify presentation if applicable, update STATUS.md, and commit the coherent change when permitted. Keep the test inputs and expected outputs in the test source, not only in prose. A failed or unavailable gate stays open.

---

## Task 5.1 — Author geographic campaign and route movement

**Files:** create `domain/Routes.h`, `Private/sim/Routes.cpp`; `core/tests/test_routes.cpp`; `content/scenarios/beta_region.json`; engine `CampaignMapView`; `content/provenance/geography.json`.

- [ ] Write validation for eight unique nodes, ten unique land pairs, one distinct coastal sea pair, sorted route sites, nonnegative lengths, and connected campaign graph.
- [ ] Acquire only a properly licensed coastline/base map with documented scale. Hand-author the eight gameplay nodes and verify they lie on appropriate land/coast. Label unverified historical names/ownership as authored.
- [ ] Implement advance/hold/withdraw/support with route progress and blocked corridors. No free off-road army movement.
- [ ] Make detailed owned settlements open from campaign nodes without resetting off-screen economies.

## Task 5.2 — Encounter contest, coherent terrain, and narration

**Files:** create `Private/sim/Encounters.cpp`, `GeneralOperations.cpp`; `core/tests/test_encounters.cpp`; route site, deployment, and narrative template content; engine `EncounterPanel`.

**Interfaces:** `ResolveEncounter` returns one persisted site/deployment/reinforcement/event result. Candidate windows are computed from positions and travel times before scoring.

- [ ] Write T21–T25 with reachable/invalid sites, unsuitable concealment, bounded better-general trials, and impossible reinforcement entry sides.
- [ ] Implement detection, initiative, site preference, concealment contest, deployment, and schedule with independent seed streams and recorded reasons.
- [ ] Add general/scout/spy support costs and effects. Infer no success solely from a high score.
- [ ] Generate the account from event templates and verify every clause against the trace and loaded battlefield.
- [ ] Integrate route encounter → existing tactical battle → committed return to campaign.

## Task 5.3 — Merchants, scouts, and faction knowledge

**Files:** create `Private/sim/Intelligence.cpp`, `Trade.cpp`; `core/tests/test_intelligence.cpp`, `test_trade.cpp`; report UI and `FactionView` implementation.

- [ ] Write T26–T27 and cargo-reservation tests. Same report repeated through two intermediaries must not count as independent confirmation.
- [ ] Implement travel/arrival-linked general reports, scout estimates, confidence/age, source retention, and exact inventory transfers.
- [ ] Hide unavailable enemy fields in all campaign UI and AI accessors. Add a test that changing an unseen enemy army cannot alter an AI decision that has no observation of the change.

**M5 exit:** movement creates actual battles with explainable general advantages, and reports are useful without omniscience.

## Task 6.1 — Collective society and staged unrest

**Files:** create `domain/Politics.h`, `Private/sim/Society.cpp`; `core/tests/test_society.cpp`; institution/estate profiles and district support UI.

- [ ] Test support under food relief versus neglect, worker war burden versus elite military standing, and protected versus harmed religious institutions.
- [ ] Implement separate material conditions, administrative reach, legitimacy, and institutional influence/support. Add top-cause explanations.
- [ ] Implement warning → noncooperation → organized opposition → rebellion with sustained conditions and recovery actions. Avoid a single unexplained "happiness 0" spawn.
- [ ] Test an honorable retreat is not automatically dishonorable and necessary defensive casualties are judged differently from repeated exploitative offensive demands.

## Task 6.2 — Alliances, coalition leadership, and diplomacy AI

**Files:** create `Private/sim/Diplomacy.cpp`, `CampaignAI.cpp`; `core/tests/test_diplomacy.cpp`, `test_campaign_ai.cpp`; neighbor and coalition screens.

- [ ] Write T28–T29 and T39, including tiny-gift loops and allied deaths assigned to the correct party.
- [ ] Implement trade, need-based aid, defensive agreement, support call/response, leadership recognition, burden memory, rewards, refusal, and withdrawal.
- [ ] Add AI economic budgets, food preservation/imports, recruitment, objectives, diplomacy, retreat, and legal construction through the same commands as the player.
- [ ] AI uses FactionView; no duplicated private "AI economy" or fake supply replenishment. Test a 20-year simulated campaign with periodic conservation checks.

## Task 6.3 — Conquest, negotiation, occupation, and regional victory

**Files:** create `Private/sim/Occupation.cpp`, `Objectives.cpp`; `core/tests/test_occupation.cpp`, `test_objectives.cpp`; siege/negotiation UI.

- [ ] Write T30–T31 and compare the same city under negotiated surrender and destructive siege. Preserve actual local structures/people/crafts and contextual support.
- [ ] Implement blockade/siege pressure using real reserves, surrender offers, ownership transfer, administrative/garrison requirements, relief/punitive choices, and district grievances.
- [ ] Field battles and negotiated takeovers function now; saved-layout manor assaults arrive in M7 rather than being falsely marked complete.
- [ ] Implement military and coalition regional objectives with a 360-day sustain check. Losing qualification resets/pauses progress according to the displayed rule; temporary capture cannot instantly win.
- [ ] Add coalition-fracture and occupation recovery playtests.

**M6 exit:** a functioning regional campaign can be won via control or coalition; social and diplomatic consequences respond to actual behavior. Full imperial politics are not added here.
