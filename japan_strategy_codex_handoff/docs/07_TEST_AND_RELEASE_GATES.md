# Verification, scenarios, and release gates

Tests in this document are requirements for the future implementation. They have not been run against a game by this handoff package. M0 must create the runner and fixtures. Documentation validation of this package is separate from game validation.

## Test levels

Portable C++ unit/property tests cover the shared authoritative model. Unreal automation tests cover importing, view bindings, construction, save integration, level transitions, and commands. Packaged manual/automated playtests cover usability, visuals, battlefield behavior, and performance. Use the engine's documented testing framework where appropriate [S05]; passing CMake tests alone cannot prove the game runs.

Implement `python tools/dev.py core-test` and `editor-test` as real wrappers. Write reports with test name, seed, content version, platform, source revision, status, and failure context. Exit nonzero on failures or unavailable required tools. Never synthesize a successful result file for a skipped operation.

## Required deterministic regression cases

| ID | Given / action | Required result |
|---|---|---|
| T01 | Same initial world/seed; advance 360 days at 1× and 10× | Same authoritative campaign state and RNG counters |
| T02 | Save at day 119; load and advance 241 days | Same result as uninterrupted day 360 |
| T03 | Available 200 workers; muster 100 | Available 100; 100 service records; living population unchanged |
| T04 | Try to muster those same people again with insufficient remaining eligible workers | Reject atomically; no duplicate IDs, equipment, or charges |
| T05 | Army of 100 uses provisions | Exactly 100 food-person-days consumed by army/day; home does not consume their rations again |
| T06 | 100 deployed; outcome 10 dead, 15 wounded, 5 captive, 70 healthy | Exactly 100 dispositions; only 10 immediate population deaths |
| T07 | Apply T06 twice | Second application AlreadyApplied; identical world state and no extra day |
| T08 | Return 70 healthy, then recover 5 wounded | Home available rises by 70, then 5; captives/wounded not prematurely productive |
| T09 | Kill two smith apprentices and no master in an exact outcome | Those cohort counts change; no fabricated master loss; output recalculates from staff |
| T10 | Allied cohort loses 12 people | Ally's origin ledger and burden change; player's unrelated workers do not |
| T11 | Routed soldiers reach escape region alive | They count as survivors/withdrawals, not dead |
| T12 | Add policy incentive to a plot without road/water access | No invalid building; inspector states access blocker |
| T13 | Build funded market at an accessible road under demand | Commercial-use attractiveness increases; funded infill can follow, not instantaneous population |
| T14 | Promote town with pinned manor/storehouse and road IDs | IDs/positions persist; no replacement city prefab |
| T15 | Auto-plan over pinned module or disconnected gate | Plan rejected or legally revised before charge; never overlap or destroy pinned work |
| T16 | Buy elite weapon without qualified staff/knowledge | Manufacturing blocked with exact reason; existing imported weapon can still exist |
| T17 | One master, bounded mentor slots, many apprentices | Apprentice training capped by supervision; no limitless elite output |
| T18 | Slaughter 10 breeding adults | Herd down 10, food up once, next birth potential lower; no duplicated working animals |
| T19 | Save before a harvest forecast, reload repeatedly | Same hidden seasonal history; forecasts reveal only observations available then |
| T20 | Block import route during regional shortage | Goods cannot arrive normally; scarcity and reserves reflect actual stocks |
| T21 | Candidate battlefield beyond either army's reachable interval | Ineligible, regardless of command score |
| T22 | 1,000 paired trials with identical context except improved scouting | Better side gains a documented statistical advantage, not guaranteed success |
| T23 | Ambush attempt on map with no valid concealment | Full concealed deployment unavailable; no hiding an army in empty plain |
| T24 | Trailing ally cannot reach battle until a later interval | No instant/flanking spawn contradicting the route; schedule records cause |
| T25 | Encounter narrative reports detected infiltrator | Event trace contains that detection and matching deployment effect |
| T26 | Enemy force is hidden from FactionView | Campaign AI and UI cannot access its exact live count/position |
| T27 | Merchant report ages without new visits | Conditions become stale; location knowledge can persist |
| T28 | Repeated tiny reciprocal gifts | Diminishing/net-need rules prevent unlimited obligation |
| T29 | Coalition member bears losses and repeated unsupported demands | Burden/grievance increases, warning and refusal/exit become possible |
| T30 | Same religious city; protect/provision institutions versus destroy them | Responses differ contextually; no universal religious calm flag |
| T31 | Larger occupied city with same admin/garrison resources | Capacity shortfall is greater without inventing extra casualties |
| T32 | Artifact exists but required metallurgy is absent | Study can identify blocker; reliable production stays locked |
| T33 | Complete artifact chain and elite training | Prototype/manufacture becomes available; ordinary levy firearm use still rejected |
| T34 | Inland settlement requests maritime district | Geography requirement fails clearly; no magic port |
| T35 | Naval crew casualties occur | Correct maritime service/cohort records, cargo, hull, and repair changes |
| T36 | Damaged/corrupt/incompatible save | Clear error; active world remains unmodified; backup available |
| T37 | Load in-battle checkpoint and continue same command sequence | Consistent same-platform outcome; no duplicate encounter or rewards |
| T38 | Fast-forward during construction with cancellations | Same inputs, progress, refunds, and occupancy as 1× |
| T39 | Normal AI for 20 years | No undocumented free supplies/troops; can seek food, replenish, retreat, and honor/decline aid |
| T40 | Lost battle plus poor harvest, with available relief/import options | At least one tested recovery policy exists; no automatic unwarned death spiral |

Property tests additionally check nonnegative stocks, valid IDs, exclusive membership, valid faction ownership, sorted site progression, no duplicate corridor pairs, no production beyond qualified capacity, and no population created by split/merge or view changes.

## Repeatable scenario suite

**Quiet growth:** no war, average weather. Build a manor neighborhood, market, and smithing expansion; promote to districts; inspect preservation of original roads and buildings. Shows that the city is pleasant before combat exists.

**Risky mobilization:** recruit farmers and some permitted artisans during a weak season. Confirm the preview, then the actual reduced labor/food resilience. Test cautious demobilization and continued war as distinct paths.

**Costly victory:** field ordinary formations plus elite samurai, win with serious losses from one craft and one warrior district. The battle report links to changed workforce, smith throughput, wounded recovery, and political grievance.

**Defeated but recoverable:** lose an army without losing all settlements. Use relief, trade, apprentices, and careful diplomacy to survive. Track population rather than granting free recovery troops.

**General's advantage:** replay seeded encounters with contrasting scouting/secrecy/coordination profiles. Verify reachable terrain and narration/deployment agreement. A weak army can receive good terrain but is not promised victory.

**Fragile alliance:** gain leadership through culture and genuine aid; call support; distribute burdens fairly in one branch and exploit the ally in another. Observe different behavior.

**Occupation:** take the same city after negotiated surrender, limited field battle, and destructive siege. Confirm district-level differences, institutional support/opposition, and capacity limits.

**Artifact laboratory:** acquired specimen with weak then mature craft capacity; validate gating, prototype consumption, reliable production, elite-only adoption, and saved progress. Clearly mark the gunpowder scenario as alternate technology.

**Sea loss:** superior versus inferior maritime capability under the same weather and seeds. Verify crew/cargo/hull accounting and regional economic effects.

## Performance protocol

Record CPU, GPU, RAM, OS, engine version, build configuration, resolution, graphics settings, thermal/power state where practical, scenario seed, unit composition, formation count, and art revision. Warm up before capture. Use at least three 120-second runs with moving formations, missiles/contact, active selection, camera pan/zoom, and reinforcement arrival. Report medians and worst meaningful tails, not only average FPS.

City fixture: 10,000 aggregate residents, 5,000 rendered ordinary/anchor structures, active infill, production, UI inspection, and camera motion. Battle release fixture: 8,000 active soldiers with realistic ordinary/elite mix, not merely static meshes. Stress fixture: 20,000 ordinary soldiers in 200 formations. Track frame time, simulation step cost, command response, peak memory, and any stalls. A CPU-only/NullRHI test is labeled simulation-only.

Target beta floor: 30 FPS at 1080p/medium on the verified reference tier, with no persistent input lag, repeated multi-second stalls, or unbounded memory growth. Compare 1st-to-3rd run memory after cleanup to catch retained worlds and actors. If the tier cannot be tested, say "unverified on reference tier" and report the machine actually tested; do not quietly certify it.

## Beta definition of done

All T01–T40 pass or an explicitly revised product decision removes the requirement; missing features cannot be waived merely to print PASS. The player completes the regional objective through at least one military and one coalition playthrough. One full run includes a poor harvest, a battle loss, an occupied city, a master-craft interruption, and a saved/reloaded tactical battle.

The packaged build includes all beta systems and scenes, usable controls/options, original or licensed assets, no core placeholder buttons, no severe pathing deadlocks, understandable alerts, tutorial, sandbox continuation, clear historical/alternate labels, credits, and a known-issues file. No crash, save corruption, duplicate-population, or blocked-campaign progression defect remains. Performance claims are supported by the published benchmark fixture and tested hardware.

A final report lists build ID, artifact path, supported/tested OS, content count, completed gates, actual test results, benchmark measurements, known limitations, and next roadmap stage. "The game should work" is not a release report.
