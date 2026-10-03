# Player interface, art, and content guidelines

## The interface promise

The game may simulate many interactions, but the player should usually make a small number of meaningful decisions. Default to direct manipulation, short forecasts, obvious risks, and useful automation. Detailed ledgers are optional drill-downs. Never expose every internal coefficient as another slider.

## Settlement view

Top strip: date/speed, population, reserve food days, treasury, materials, stability warning, and military readiness. Main actions: roads, major structures, expansion modules, broad policy, and muster. Selecting a building shows two or three actionable choices, their costs, expected local effects, and missing requirements. A plot overlay answers "why nothing is growing here" with the strongest limiting reason.

Selecting a district shows its character, population, major work, investment, security, and war burden. A comparison preview for recruitment reports actual occupations removed and likely consequences. "Protect essential workers" is on by default. Opening a details drawer reveals cohort counts and jobs without requiring household-by-household decisions.

Town promotion is deliberate. The button appears when eligible, with its administration costs and the automation it enables. It cannot remove manual control over major roads or original buildings. Pin/unpin is explicit. Automated manor designs show a ghost preview and itemized resource budget before confirmation.

## Military interface

Use an army browser with grouped rows and filters rather than an endless unstructured row of 150 unit cards. Default groups: main line, missiles, elites, cavalry, reserve, and allied contingents. Group selection must not make individual units inaccessible.

A selected formation shows role, personnel, morale, fatigue, quality, ammunition, and district/occupation origin. Hover a visible individual for their origin label; do not render thousands of nameplates all the time. A casualty list can filter by district, occupation, skill, or estate.

Essential controls: WASD camera pan, middle-drag rotate, wheel zoom, left select, shift additive selection, box select, right move/attack, right drag frontage, shift waypoint, ctrl-number group, number recall, space pause. Remapping, adjustable camera speed, edge-scroll toggle, and UI scale must be in beta. Resolve contextual drag ambiguity with a clear formation preview and cancel key.

## Campaign and encounter interface

The campaign map shows cities and routes; no free drag-to-anywhere movement. Blocked corridors and alternative node paths are obvious. Targeting an army shows its orders and known facts, not exact hidden enemy state.

An encounter preview gives a short three-to-five-line operational account, terrain thumbnail, known opponent estimate, force origins, supply, deployment advantages, and reinforcement uncertainty. A details expander exposes the recorded reasons. Avoid fake dramatic text contradicting the tactical setup. Autosave before commitment.

## Aftermath: the signature screen

Headline victory/defeat is followed by what it cost the society. Show deployed, healthy, wounded, dead, captive, missing, and deserters distinctly. Break out origin districts/occupations and allied burdens. Link directly to affected city areas.

Example layout: "East Forge Quarter: 12 workers dead, 9 recovering, 4 captive; 1 master still absent; current tool output limited by qualified labor." Values must come from state. Do not hardcode "-11% weapons" merely because the scenario designer wanted drama. Suggested responses include demobilization, apprentice support, relief, import, or negotiation, with real costs.

## Diplomacy and institutions

A neighbor screen shows relationship character and remembered actions, not just one magic loyalty bar. Calls for aid show need, requested amount, likely burden, and existing obligations. Coalition members display accumulated contributions and what they believe they are owed. The player can be recognized as leader without individually flattering dozens of characters.

Society panels show the top sources of support and grievance. Religious networks and warrior interests are institutional. Show why a temple supports surrender or resists, not an inherent obedience score tied to religion.

## Artifact and maritime panels

Artifact panel: source, date, authenticity/interpretation certainty, historical/alternate label, known prerequisites, study/prototype/manufacture state, workshop availability, projected cost, and blockers. A research bar alone is insufficient. The normal campaign and alternate artifact laboratory are clearly distinguished.

Sea report: convoy, escort, ships, crews, cargo, relevant maritime capability, observed enemy information, encounter reasons, losses, and repair needs. No scene needs to pretend a naval RTS exists.

## First-session guided experience

Make the introduction event-driven, not a scripted promise that all players will hit a certain minute. The player places a manor addition, connects a road, chooses food versus craft investment, sees households fill accessible plots, supports an apprentice, receives a merchant report, answers an aid request, and raises a small force with visible labor costs. The first battle and aftermath demonstrate consequences before the tutorial considers itself complete.

Do not force a terrible harvest on every first campaign; use a repeatable training scenario for that lesson. The main scenario can produce good and bad years through its actual weather model.

## Art and atmosphere

Beta uses original or properly licensed stylized early-medieval Japanese assets with clear silhouettes, consistent scale, and readable terrain. Manor complexes, timber/earth defenses, fields, sacred spaces, craftsmen, clothing, and mounted elites establish the setting. Source period-specific references before dressing the map like a sixteenth-century castle town.

At least distinct walking, idle, attack/volley, rout, and death states are visible by the final beta. Simple animation is acceptable; frozen statues sliding through battle are not. Ordinary structures require variation in roof, frontage, orientation, and age. Seasonal cues and construction progress should be visible. Weather must not hide tactical readability.

Use inexpensive visual markers and formation banners without copying Total War unit cards or interface art. Do not distribute font files or unlicensed marketplace content. A licensed external asset is not automatically historically appropriate.

## Asset pipeline

Record asset ID, source URL if external, author, license, permitted distribution, attribution, date, modifications, period fit, and importer version. Use original geometric meshes for the first technical milestones. Prefer repeatable generation/import tooling; never create nonexistent `.uasset` references by text. Engine-created assets must be generated and opened/validated in the actual installed engine.

The final beta contains terrain, water, roads, ordinary buildings, twelve anchor families, eight manor module families, five troop roles, trees/crops, equipment silhouettes, key UI icons, music/ambience with appropriate licensing, and basic feedback sounds. Performance budgets include all of these, not only graybox tests.

## Accessibility and clarity

Color is never the sole state indicator. Provide readable fonts, UI scaling, contrast, subtitles for any spoken line, reduced camera shake, pause access, alerts that do not vanish during fast-forward, and a compact event history. Destructive decisions and emergency recruitment have previews. Blocking alerts are configurable, with a sensible default for attacks, critical food, rebellion warnings, and alliance ultimatums.
