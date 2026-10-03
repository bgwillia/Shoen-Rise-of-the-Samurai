# Technical architecture and data ownership

## Decision A01 — Engine default, not an untested performance promise

For a fresh project, use an installed stable Unreal Engine 5 release with C++. Record its exact version in `toolchain.lock.json`; do not automatically upgrade an existing project. Unreal provides instanced mesh representation, data-oriented Mass systems, and automation facilities, which are useful building blocks, not proof that this game's target scale will work [S02–S05 in the source notes]. Do not make a paid RTS framework or an unavailable editor MCP integration a dependency.

Use C++ for the authoritative model and most gameplay wiring. UMG/Slate, materials, original meshes, and optional thin Blueprints handle presentation. Blueprints do not own separate population, treasury, or combat truth. If an existing Godot/Unity/other game already implements the right mechanics, audit its suitability and map these contracts rather than destroying it; a fresh web dashboard is not an acceptable substitute.

## Proposed repository layout

```text
game/DomainGame.uproject
game/Source/DomainCore/DomainCore.Build.cs
game/Source/DomainCore/Private/DomainCoreModule.cpp
game/Source/DomainCore/Public/domain/Types.h
game/Source/DomainCore/Public/domain/World.h
game/Source/DomainCore/Public/domain/Commands.h
game/Source/DomainCore/Public/domain/Content.h
game/Source/DomainCore/Public/domain/Population.h
game/Source/DomainCore/Public/domain/City.h
game/Source/DomainCore/Public/domain/Economy.h
game/Source/DomainCore/Public/domain/Crafts.h
game/Source/DomainCore/Public/domain/Recruitment.h
game/Source/DomainCore/Public/domain/Battle.h
game/Source/DomainCore/Public/domain/Routes.h
game/Source/DomainCore/Public/domain/Politics.h
game/Source/DomainCore/Public/domain/Discovery.h
game/Source/DomainCore/Public/domain/SaveCodec.h
game/Source/DomainCore/Private/sim/  # corresponding pure C++ implementations
game/Source/DomainGame/            # engine integration, input, UI, views
game/Content/Domain/              # real generated/editor-created engine assets
core/CMakeLists.txt                # builds the SAME Private/sim sources
core/tests/
content/definitions/              # validated authoring JSON
content/scenarios/
content/provenance/
tools/dev.py
artifacts/
docs/execution/
STATUS.md
```

`DomainCoreModule.cpp` is only the Unreal module bootstrap. Everything in `Public/domain/` and `Private/sim/` must compile without Unreal headers. The portable CMake target excludes the bootstrap. Do not implement an independent Python economy or a second battle model for tests. Unreal's JSON importer converts authoring data into shared plain-C++ definitions; core unit fixtures construct the same types, and integration tests verify the imported definitions.

## Decision A02 — Persistent model, replaceable views

A persistent game-instance subsystem owns one `domain::World`, scenario content, and the command/event queues. City, strategic-map, and battle levels are views over that state. Opening a different view cannot restart the economy, reseed weather, or duplicate soldiers.

Use three scenes with consistent art and transitions: regional campaign map, detailed settlement, and tactical battlefield. The full game may improve zoom transitions, but a literally seamless terrain is not required. Load a settlement from its saved layout. An assault builds the battlefield from that same layout plus an authored surrounding apron. Multiple owned cities can be loaded one at a time; off-screen cities still run the same aggregate rules.

## Decision A03 — Time and reproducibility

Campaign advances in discrete integer day steps. Events within a day have a stable phase and sequence order. Speed changes alter the number of day steps processed, not production formulas. Do not skip days when fast-forwarding. If a performance backlog grows, display that the game is running slower rather than silently skipping simulation.

Separate RNG streams for weather, migration, organic placement, recruitment selection, encounters, combat, and diplomacy; persist every stream and counter. Same-build/same-platform reproducibility is required. Cross-platform bitwise tactical replay is not promised: floating point navigation and engine physics must not be presented as inherently deterministic. Use integer/fixed-point quantities for authoritative economy and a stable canonical ordering for hashes.

Tactical commands run at a fixed 20 Hz, with formation decisions at a lower staggered rate and visuals interpolated. The campaign is frozen while tactical play runs. One encounter transaction owns its operational-day increment.

## Decision A04 — Civilian cohorts, deployed service records

A cohort is keyed by settlement, district, occupation, skill, estate, and age/service eligibility band. Civilians live as counts. A soldier record is created only when someone enters service, referencing the cohort and retaining origin even after transfers or city conquest. Service record IDs are stable and never recycled within a campaign.

Maintain exact counts with exclusive service statuses. The global living population consists of home residents plus living people away in service, captivity, or known displacement. Dead records remain in an audit ledger, not the living population. A formation holds service IDs or ranges into a registry; it never creates a second copy of those people.

A unit inspector can show origin breakdowns or inspect a selected soldier. Names may be generated reproducibly for display, but do not add individual civilian AI, biographies, or relationship state.

## Decision A05 — Formation simulation, scalable representation

One controller per formation selects path, facing, frontage, target, and state. Slot positions are derived from formation pose and rank/spacing; local correction is bounded. Use terrain and obstacle navigation at formation level, with special choke states at gates/bridges. Do not run navigation or full collision for every person.

Combat uses contact fronts, facing, density, weapon role, experience, morale, fatigue, and seeded hit allocation to actual eligible service records. Preserve meaningful frontage and rear attacks rather than applying global damage to whole armies. Use a spatial grid for nearby formations and volley target regions. Avoid all-pairs soldier checks. Contact-area width limits how much of a formation can fight at once.

Rendering backend begins with batched instances and simple original animated or pose-varied soldier meshes. Evaluate vertex animation or a bounded near-camera skeletal pool during M0; never require one skeletal component per soldier. MassEntity/MassRepresentation is an option behind a representation adapter, not a compulsory new framework before a baseline benchmark. Epic documents instancing and Mass features [S02–S04]; the project must measure its actual costs.

Logical casualties and transforms cannot depend on whether a soldier is visible. At wide zoom, LOD can simplify silhouettes and animation; it cannot delete simulated forces or change battle outcomes. Bound corpses, ragdolls, particles, arrows, audio voices, and selection labels. Off-screen soldiers continue to matter.

## Decision A06 — Exact interface boundaries

Implement these public concepts before adding features that depend on them. Names can be translated for an existing codebase only in a recorded interface map.

```cpp
namespace domain {
using EntityId = std::uint64_t;
using Day = std::int64_t;
using Quantity = std::int64_t;
struct World;
struct Content;
struct Command;
struct CommandResult;
struct FactionView;
struct EncounterRequest;
struct Encounter;
struct BattleState;
struct BattleCommand;
struct BattleOutcome;
struct ApplyResult;
struct Snapshot;
struct DecodeResult;

CommandResult ApplyCommand(World&, const Content&, const Command&);
void AdvanceOneDay(World&, const Content&);
FactionView ObserveForFaction(const World&, EntityId faction);
Encounter ResolveEncounter(World&, const Content&, const EncounterRequest&);
BattleState StartBattle(const World&, const Content&, const Encounter&);
void StepBattle(BattleState&, const Content&, std::span<const BattleCommand>);
BattleOutcome FinalizeBattle(const BattleState&);
ApplyResult ApplyBattleOutcome(World&, const Content&, const BattleOutcome&);
Snapshot MakeSnapshot(const World&);
std::vector<std::uint8_t> EncodeSnapshot(const Snapshot&);
DecodeResult DecodeSnapshot(std::span<const std::uint8_t>, const Content&);
}
```

These are contract sketches, not included compiled code. Define complete types and error variants in the relevant task. `StepBattle` advances one fixed step; the caller does not supply arbitrary delta time. `FinalizeBattle` produces statuses, not direct city mutations. `ApplyBattleOutcome` is the single transaction owner and rejects repeat IDs or foreign/stale inputs. `ObserveForFaction` is the only knowledge surface for strategic AI and the enemy UI.

## Decision A07 — Transactional transitions

Recruitment validates eligibility, equipment reservation, budget, and muster capacity before mutating anything. Cancellation releases reservations exactly once. A battle stores battle ID, world revision, army IDs, initial service IDs, encounter seed/result, committed result flag, and operational-day flag.

Battle outcome validation proves every participating service record has exactly one final disposition and all equipment/cargo changes are bounded. On apply, update service records, cohort counts, health states, equipment, political events, and world revision as one transaction. Reopening a result panel does nothing to state. Reloading a pre-result save must not produce duplicate casualties or reward rolls.

## Decision A08 — Save format and safety

Save stable IDs, content/version identifiers, all RNG state, commands waiting to execute, production queues, plots and pinned structures, knowledge, alliances, occupation histories, military registries, pending/active encounters, tactical snapshot where applicable, and applied transaction IDs. Pointer addresses and scene actor identities are not save keys.

Use a versioned, length-bounded portable snapshot encoding. Validate lengths, enum values, counts, references, checksums, and content compatibility before replacing the current world. Do not deserialize arbitrary executable types. Saving uses a stable snapshot copied at a safe boundary, with a temporary file and replace only after successful serialization. Keep one backup. Unreal's asynchronous save facility can write the payload without a gameplay hitch [S06]; it does not make concurrent mutation of the captured state safe by itself.

Beta must support campaign saves, a pre-battle autosave, and a battle checkpoint at a fixed-step boundary. If an active-battle save cannot be restored, the release gate is open; do not quietly claim midbattle support. Version upgrades require a migration test or a clear incompatibility message.

## Decision A09 — Content and errors

Store balancing data outside C++: resource definitions, building modules, influences, equipment recipes, training requirements, unit archetypes, route sites, society weights, artifacts, and scenario seeds. Treat provided JSON examples as illustrative contracts, not magically loaded files. Validate unique IDs, nonnegative quantities, dependency cycles, valid route endpoints, coastal requirements, unit equipment, chronological/alternate flags, and references before play.

UI errors state the failed requirement and leave the world unchanged. Reject invalid construction footprints and unreadable content with actionable diagnostics. Missing optional art uses a labeled development fallback; missing core definitions block scenario start. No success toast on a failed action.

## Decision A10 — Performance acceptance

Provisional reference tier: one contemporary desktop CPU, 16 GB system RAM, and one approximately RTX 3060-class GPU at 1080p/medium. The first audit records actual hardware and cannot claim this tier was tested on a stronger or weaker machine. No dual-GPU assumption.

Aim for a 30 FPS floor in the beta's 8,000-soldier fixture and a responsive city with 5,000 visible buildings/10,000 aggregate residents. Report median and 95th-percentile frame time, simulation CPU, memory, GPU timing where available, selection latency, and stalls. These are validation targets, not guarantees. Profile 20,000 soldiers separately. Performance acceptance must use actual animated movement/contact/commands, not a static array or NullRHI run.
