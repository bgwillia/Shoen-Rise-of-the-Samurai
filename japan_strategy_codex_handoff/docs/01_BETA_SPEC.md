# Playable beta specification

All quantities in this document are initial tuning defaults. They are not historical population estimates, physiological constants, or measured performance claims.

## Deliverable

A packaged offline desktop game with a complete regional campaign, a guided introduction, a battle laboratory, save/load, options, tooltips, basic audiovisual feedback, and an honest credits/provenance screen. A coherent simplified 3D art style is acceptable. Unlabeled cubes, nonfunctional menus, mock casualty reports, or a terminal-only simulation are not the finished beta.

The campaign must connect city growth, risk, craftsmen, military origins, route encounters, tactical combat, political consequences, and recovery. The beta must contain the following systems in playable form; their deeper variants belong to the roadmap.

## Setting and map

Use a small region around the eastern Inland Sea / Osaka Bay as a **geographic prototype selection**, not a claim that this handoff provides a researched 1180 political map. Include a recognizable Japan overview with the playable region highlighted. For the playable region, use real coastline and broad terrain, then author eight scenario nodes on that geography. Their initial names describe their gameplay function until exact period names and ownership are verified.

There are four houses: one selectable player scenario and three AI houses. Each begins with two settlement nodes. Start the player with a 420-person manor center and a 1,680-person subordinate agricultural settlement; the 2,100 total is the entire starting domain, not 420 people somehow supporting an army of thousands. Other faction sizes and capacities are balance data. Births, deaths, and net migration must account for growth; population cannot jump at a promotion.

Use ten unique land edges and one sea connection between **different endpoint pairs**. No duplicate land route per city pair. Only coastal nodes may touch the sea edge. Land routes reference two or three ordered site definitions drawn from four authored terrain families: open farmland, river crossing, wooded ridge/pass, and town approach. Reuse modular terrain families with route-specific landmarks, orientation, weather, and deployment variants rather than hand-building thirty unique maps initially. Beta does not permit a normal army to bypass a blocked land corridor through scenery.

One port is the overseas contact gateway. External regions are off-map contact records, not additional playable maps. None of the unverified placeholder nodes should be marketed as an authentic named historical settlement.

## Settlement and progression

Every owned important node can be opened in a detailed settlement view, but only the capital needs active fine-grained management; the same rules run in aggregate for delegated towns. The eight nodes include a port, a religious center, a craft opportunity, an agricultural hinterland, and a mountain corridor.

Initially allow direct building placement, roads, farm plots, staffing priorities, and construction queues. Residents and small workshops can also fill approved street frontage. District administration becomes available at 1,200 residents in the town center, a functioning administrative expansion, stable housing/water access, and a funded promotion project. These are defaults, not hardcoded engine limits. Eligibility should warn about food risk, not forbid a deliberate risky promotion solely because reserves are low. Promotion enables broader policies and automation; it does not spawn population or replace buildings.

Use a hidden 4-meter occupancy raster to simplify collision and parcel finding, with visible free-angle roads, contour-aware footprints, rotated buildings, and nonrectangular block boundaries. It is not a visible square-grid city aesthetic. At first implement street-front parcel subdivision, not a generalized urban procedural research project. District IDs are stable administrative groupings; their labels and dominant uses emerge gradually from actual activity. Split/merge is deferred, but the data model must not confuse district identity with use type.

Allow mixed uses and four soft priorities: agriculture, commerce, crafts, and retainer support. Religious and maritime anchors add additional demand/influence where appropriate. Policies have costs and saturating effects. Preserve player-pinned structures and reserved construction corridors. The player can see why a plot grows or remains empty.

## Beta building vocabulary

Twelve functional anchor families: manor/administration, market, granary, smithing compound, training/retainer compound, shrine, temple, water/irrigation works, livestock yard, lumber/charcoal compound, harbor/shipyard, and road/gate infrastructure. Ordinary housing, small shops, and small workshops use the infill system. Store military equipment through a manor or smithing expansion rather than a separate management minigame.

At least six anchor families offer two meaningful alternative additions. Required choices: market storage versus merchant hall; smith apprentice court versus extra production forge; manor administration versus retainer court; temple relief store versus study hall; granary capacity versus preservation; harbor cargo yard versus shipwright yard. Infrastructure constraints and ongoing costs apply.

Manual/automatic manor planning shares eight piece families: residence/hall, courtyard, palisade, gate, watch platform, storehouse, stable, and well. Earth banks can be fixed terrain/buildable modules; freeform terrain sculpting is deferred. The auto planner offers compact defensive and administrative layouts, respects pinned pieces, previews costs, and is cancelable. One playable manor assault must use the saved wall/gate/building layout with basic pathing and gate damage. Full siege engineering is not required.

## Economy and people

Visible headline resources: food reserves, treasury, timber, iron, fuel, and equipment. Horses and livestock are separate biological ledgers; population is a cohort ledger, not spendable inventory. Equipment retains type, quality band, quantity, and origin batch. Research is institutional capability, not another generic resource counter.

Six occupations: agriculture, general labor, smithing, commerce, maritime work, and retainer service. Smiths additionally have apprentice, trained, and master skill bands. Other occupations can use novice/trained/expert bands where relevant. Estates identify ordinary households, merchant interests, warrior interests, and religious institutions without assigning every resident an individual political character.

Rice-centered food abstraction, seed protection, storage losses, planting/growth/harvest phases, region-correlated weather risk, progressive forecasts, herd growth, and emergency slaughter must work. The beta uses abstract food person-days, not unsourced koku conversion. Livestock species and dietary framing remain content-profile choices; do not imply an intensive cattle-meat industry is universal 1180 Japan.

Smith production distinguishes equipment quality from volume. Training uses mentor capacity and accumulated work, not merely calendar time. A real interruption from casualties or conscription must reduce output. Protect scarce specialists by default, with an explicit emergency override and forecasted consequences. Maintain tools for food production as a competing smithing demand.

## Army and combat scope

Five main formation roles: ordinary polearm infantry, ordinary bow infantry, trained retainer infantry, elite samurai foot troops, and elite mounted samurai archers. A scout/stealth support detachment influences operations without requiring a sixth micro-heavy tactical role. New combat roles require new production and training rules, not just a renamed prefab.

Standard formations begin at 100 soldiers; elite foot formations at 40; mounted elites at 32. Content can configure 60–160 ordinary or 24–60 elite soldiers. These are gameplay scales. Units are never automatically inflated to keep unit-card counts low. Every active formation remains individually selectable; grouping reduces input burden, not simulation count.

The packaged beta target is **8,000 concurrently simulated and represented soldiers total**, typically roughly 80–120 formations depending on composition. The performance laboratory additionally measures **20,000 total soldiers / 200 100-person formations**; it is a stress result, not automatically a release promise. Full-game architecture targets more after evidence-based expansion. The beta campaign need not reach 8,000-person battles immediately; labor, recruitment, ally support, and equipment must justify every deployed person.

Movement, facing, frontage, melee contact, arrows, ranged visibility, cavalry charges, terrain, morale, fatigue, cohesion, routing, retreat, and timed reinforcement must function. Use readable simplified animation first, not synchronized cinematic kill duels. Elite samurai are strong, but can be flanked, exhausted, isolated, or overwhelmed.

## Campaign, politics, and sea scope

Daily corridor movement with four orders: advance, hold, withdraw, and support. Scouts and concealment are pre-encounter posture/support choices, not a second free-movement game. A general's six attributes affect bounded operational contests; all map choices must be physically reachable.

Merchant and scout reports contain observed time, source, confidence, and estimates. General narratives are generated from actual encounter events and can be replayed from the saved result. Diplomacy supports trade, grain/equipment aid, defensive alliance, request support, honor/refuse support, coalition leadership recognition, and withdrawal from a coalition. Occupation supports negotiated surrender, assault, siege pressure, restraint/relief, and punitive extraction with real district consequences.

A sea route supports trade convoys and military escort/interception, using transparent simulated resolution. Ship production/repair requires a harbor, shipwright labor, materials, and time. Sea losses affect crews, cargo, ships, and the port economy. There is no playable naval RTS in this beta or an implied requirement for one later.

## Artifacts and learning

One normal campaign artifact chain must work end to end, using an imported craft specimen or navigational/surveying instrument labeled as an authored example unless researched. Acquisition, inspection, prerequisites, study, prototype cost, production validation, and local manufacture are separate states. A controlled alternate-technology laboratory scenario exercises the same chain with a fictionalized foreign gunpowder specimen and elite-only training. It does not silently populate the standard 1180 campaign with later firearms. No real manufacturing recipes are part of the content.

## Time and game modes

Use a deliberately simplified 360-day calendar, explicitly identified in settings as a simulation calendar. Initial speed is 1 simulated day per 3 real seconds at 1×; pause, 1×, 3×, 5×, and 10× are available. A year is therefore 18 real minutes at 1×, 3.6 at 5×; these are tuning values. Process the same fixed day steps at all speeds rather than enlarging the timestep.

Tactical combat uses its own fixed 20 Hz simulation with visual interpolation. Campaign time freezes while a land battle is played; reinforcement arrival times are locked when the encounter is created. Commit one configured operational day after resolution. This is an explicit single-player time abstraction: do not run years of harvest or train apprentices while the user pauses a battle. Sea autoresolves use the same operational-day accounting. Never apply that day twice after reload.

Campaign designed for 15–25 simulated years with multiple battles; sandbox continues afterward. Growth must be supported by migration and resources, not a guarantee of reaching a target population on a clock. Apprentice development is accelerated but multi-year; biological and craft times are separately tunable and explained.

## Scenario completion and failure

The regional objective is to retain a functioning capital and either control four of eight nodes or lead a coalition recognizing authority over at least five. Maintain that position for 360 simulated days while meeting food solvency and no active capital revolt. Victory is "Regional Hegemony," not emperor. Offer continued sandbox play.

Lose when the player controls no settlement and no viable allied refuge, or when a successful internal usurpation removes the ruling authority after a clearly warned crisis. One lost field battle is recoverable. Supply and casualty loops must allow rational retreat, reconstruction, migration, and renewed diplomacy.

## Release scope boundary

Full-Japan politics, imperial coronation, hundreds of artifacts, multiple era packs, elaborate judicial disputes, formal duel cinematics, advanced covert institutions, sophisticated district splitting, naval tactical control, and individual family drama are outside the beta. Their core data interfaces are preserved where they are genuinely needed; no empty giant subsystem is required.
