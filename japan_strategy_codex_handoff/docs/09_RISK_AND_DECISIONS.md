# Decisions, risks, and scope protections

## Proposed defaults, not additional user approvals

| Decision | Default and rationale | Revisit trigger |
|---|---|---|
| Engine | Unreal Engine 5/C++; large 3D presentation with shared portable core | A suitable existing project or measured tooling blocker |
| Platform | Single-player desktop; verified host first, Windows preferred final target | A real tested additional target |
| Beta region | Eastern Inland Sea / Osaka Bay geographic prototype | Historical-content audit before naming exact 1180 factions/nodes |
| Map scale | 8 nodes, 10 land edges, 1 sea edge, 4 terrain families | Beta loop and AI complete before adding content |
| Population | 420-person capital plus 1,680-person hinterland | Balance, not historical validation |
| Formation size | 100 ordinary, 40 elite foot, 32 mounted; data-driven | Tactical readability without increasing into giant formations |
| Battle target | 8,000 total release fixture; 20,000 stress fixture | Measured render/simulation/UI performance |
| Time | 360 days/year; 3 real seconds/day at 1×; fixed tactical clock | Playtests of growth, training, and decision frequency |
| Victory | Regional hegemony in beta; emperor in full alternate-history game | User explicitly changes goal |
| Naval | Operational resolution, no naval RTS | Separate explicit product decision |
| Artifacts | One normal chain; separate alternate gunpowder lab | Researched and balanced additional content |

## Risk register

**R1: Many small formations are computationally and cognitively expensive.** Prove movement, contact, rendering, and group controls in M0/M3. Do not benchmark only idle graphics. Keep soldier origins independent of renderer. Escalate a failed performance target with measurements, not a hidden change to unit sizes.

**R2: The city-battle ledger can duplicate people or remove labor twice.** One authoritative service registry, exclusive status transitions, and idempotent battle transactions. Test killed versus wounded versus captive versus routed and allied casualties before more unit types.

**R3: Too many systems undermine a quick city builder.** Preserve few primary actions, policy presets, strong previews, automation, and optional detail. An institution requiring ten new permanent sliders needs simplification. Cut content variants before core causality.

**R4: A flat template generator produces bland cities.** Preserve roads, terrain, anchors, frontage, mixed uses, and pinned history. Use a constrained parcel algorithm first, but require visible variation and locality. Do not spend the beta inventing general-purpose procedural architecture.

**R5: Auto castle construction fails during actual battles.** Share validation and layout storage. Test gate pathing and assault on the same player layout. No successful auto-design without valid entry and reachable critical structures.

**R6: Generic honor/religion mechanics become misleading and unfun.** Contextual values and institutional support; no guaranteed fanaticism or obedience. Distinguish battlefield loss, avoidable sacrifice, civilian harm, and necessary retreat. Mark deliberate fictional rules.

**R7: Generals become a dice roll that overrides player agency.** Bound advantages, constrain geography, expose reasons, keep tactical control, and verify statistical rather than guaranteed superiority. Avoid arbitrary reinforcement sabotage.

**R8: Scaled military losses cause an unrecoverable death spiral.** Protect key specialists by default, distinguish recoverable wounds, make retreat possible, allow relief and migration, and test recovery. Do not erase serious consequences merely to make all choices safe.

**R9: A headless agent claims a visual game is complete.** Separate model tests, engine launch, packaged play, and render benchmarks. Record missing editor/GPU access as blocked. Supply portable work without pretending it verifies presentation.

**R10: Full-game ambitions consume the beta.** Each expansion stage has exit gates. No worldwide playable ocean, dynasty simulator, cinematic duels, advanced imperial politics, or fifteen religions before the beta loop works.

## Change protocol

Record changes as: original requirement, observed problem, alternatives considered, chosen revision, impact on saves/tests/content, and approval status. User requirements need explicit approval to change. Numerical tuning may change with recorded evidence. An environment problem justifies adapting implementation, not silently changing the game's identity.

## Full-game extension seams worth preserving now

Stable origin IDs; content-driven recipes and unit archetypes; contextual institution profiles; route/site definitions; encounter events; artifact stage/capability schemas; geography tags; relationship memories; versioned saves. These are used in the beta already. Do not add unused abstract factories, twenty empty services, or speculative distributed infrastructure merely because the full game is large.
