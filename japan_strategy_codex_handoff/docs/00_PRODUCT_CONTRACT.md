# Product contract: protected full-game vision

## Identity and priorities

A quick-to-play, organically growing Japanese city builder with large real-time formation battles and a deliberately simple campaign movement model. The inspirations describe interaction goals, not assets, branding, code, or a requirement to reproduce commercial games exactly.

The order of priorities is: understandable city decisions; satisfying tactical control; real city/war consequences; meaningful specialization and risk; historical atmosphere with deliberate alternate history; scalable presentation. Do not turn the project into a dynasty RPG, a logistics micromanagement simulator, or a fully agent-simulated city.

## P01 — Real geography, authored historical scenario

The full map is Japan, starting approximately 1180. Real geographic structure matters, but the world is not required to be a continuously loaded, one-to-one terrain model. Historical research and gameplay reconstruction must be distinguishable. Era-appropriate manor compounds are the initial visual baseline; later monumental castles need an appropriate later or alternate-development context.

## P02 — Persistent settlement identity

Begin with direct placement of a modest manor settlement. When requirements are met, the player deliberately enables district administration. Original buildings, roads, names, and IDs persist. The city never gets replaced by a different prefab at a level threshold. At scale, major structures and infrastructure remain player-placed; ordinary development increasingly fills in automatically.

## P03 — Soft influence, not rigid zoning

Road access, water, security, jobs, wealth, demand, policy, and major institutions influence growth. Neighborhood character is an outcome, not a mandatory single-use zone. Policies bias suitable uses rather than creating free demand or forcing every plot to one use. A district can be mixed, change character, and preserve its name/history. Pinning a hand-built structure protects it from automatic replacement.

## P04 — Landmark modules and manual/automatic castle design

Major buildings gain physical additions at development milestones. Their expansion affects surrounding demand and services, with costs and tradeoffs. Manor planning has automatic and manual modes that use the same pieces, rules, resources, and saved layout. Players can switch modes; auto-planning respects pinned work. The defensible compound is reproduced in an actual assault, not replaced by a generic castle map.

## P05 — Economy as deliberately risked resilience

Food, seed, livestock, treasury, worker availability, materials, and knowledge provide resilience. The player can consume these to pursue weapons, elite training, learning, or war. Harvest signals develop during the season; the game does not reveal next year's exact outcome. Emergency slaughter buys food at the cost of future herd growth or work capacity. Famine, labor loss, desertion, migration, and unrest are related but distinct states.

## P06 — Human skill limits production

Blacksmiths strongly determine feasible equipment, production scale, quality, and training capacity. Quantity is not the same as craftsmanship. Skilled workers, apprentices, materials, fuel, workshops, and retained knowledge are separate constraints. Training and specialization compound; losing workers can damage capability for years. Extend this pattern to other crafts without making players manage individual friendships.

## P07 — Fast collective civilian simulation

Civilian population is aggregated into district/occupation/skill/estate cohorts. Decorative workers are presentation, not economic authorities. Important specialists may have names or registry entries, but the UI manages staffing policy and institutions. No mandatory household or samurai relationship micro-management.

## P08 — Many small military formations

Players directly control small formations in Shogun-style battles, including line width, facing, groups, reserves, charges, missile use, retreat, and reinforcements. Large armies come from many formations. Do not revert to 500–800 soldiers per formation or a hard 20-card limit. Preserve formation-level AI and efficient soldier presentation; not every person needs an independent decision-making brain.

## P09 — Exact military origins and consequences

Every mobilized service record retains origin settlement, district, occupation, skill cohort, estate, equipment, and current status. Those records can be inspected without managing their lives. A formation's district label is not just flavor. Exact deaths, injuries, captivity, and desertion alter the corresponding home population and labor. Surviving a rout is not death. Allied losses return to the ally, not the player's capital. Do not relabel origins when formations merge.

## P10 — Developed, distinctive, counterable samurai

Samurai have a substantially higher development ceiling through training, culture, experience, horses, armor, and exceptional weapons. They should strongly influence battle outcomes, but remain human-sized formations with ammunition, fatigue, morale, exposure, and replacement constraints. Ordinary formations stay mechanically simple but useful. All district types can support military excellence through investment; occupation must not deterministically assign innate combat skill.

Samurai collectively judge military stewardship, rewards, protection, legitimacy, and losses. Their influence can cause disobedience or rebellion. No marriage, personal favor, or dialogue system is needed for each samurai. Represent the user's "samurai values" through contextual expectations, not an assertion that one immutable historical honor code governed everyone.

## P11 — Artifacts before technical adoption

Physical specimens, texts, artisans, and external contact can reveal technical possibilities. Adoption requires research capacity, appropriate knowledge, skilled production, inputs, and training; an artifact alone grants no mass production. The game must distinguish studying, prototyping, validating, and producing. Elite/samurai-level units are required for gunpowder use in the intended ruleset, an explicit balance choice rather than a universal historical fact. Do not silently replace it with mass levy gun units. Avoid real-world weapon-manufacturing instructions: model prerequisites and production abstractly.

## P12 — Restricted routes and coherent encounters

Each directly connected city pair has one land corridor. Armies contest that corridor and cannot routinely walk around opponents. Distant graph detours through other settlements are possible. Multiple battlefield sites lie along the same corridor, not on alternative roads. Encounters depend on reachable positions, timing, generals, scouts, stealth support, and intelligence. Better command improves opportunities; it never teleports armies or gives guaranteed wins.

## P13 — General narrative explains real resolution

Generals have command, coordination, scouting, secrecy, terrain, and logistics strengths. Their operational resolution produces the actual deployment, surprise, and reinforcement conditions. A short account explains those causes. Every sentence must derive from recorded events; no invented success narrative after unrelated dice. Spy/stealth capability is an abstract support system, not mandatory agent micromanagement. Dedicated stereotyped ninja institutions are not automatic 1180 content.

## P14 — Information has sources, age, and uncertainty

Merchants report broad settlement conditions and travel observations; scouts report military conditions; allies share selectively. Known settlement existence persists, but conditions go stale. The AI receives an information view too, not omniscient truth. Merchant intelligence must not reveal exact hidden armies merely because a trade connection exists.

## P15 — Collective society, culture, and religion

Food satisfaction, order, autonomy, prosperity, cohesion, institutional influence, and legitimacy can vary independently. Religion and culture create learning, aid, prestige, travel, political support, and independent power. A religious town can recover peacefully when its institutions support the settlement; religious affiliation is not an unconditional calm modifier. A supported institution may also organize opposition when harmed. No intrinsic religious or class-based obedience stereotypes.

## P16 — Occupation remembers how the city was taken

Size, institutions, living conditions, losses, siege suffering, destruction, exposed covert activity, promises, restraint, relief, leadership legitimacy, and administrative capacity affect control. Keep district differences. A garrison can suppress disorder without removing resentment. Negotiated settlements and honorable treatment are viable, while starvation and destruction create real hostility.

## P17 — Alliances through trust, obligation, and fair burdens

Help, services, battle support, relief, kept promises, and cultural prestige create relationships. Powerful militaries or smaller culturally respected powers can lead coalitions. Recognition as leader is accessible; sustaining it is difficult. Repeated demands, casualties, ignored needs, broken promises, and unfair rewards can fracture alliances. Friendly armies do not magically coordinate: generals and actual arrival times matter. No spam-gift exploit or compulsory permanent alliances.

## P18 — Maritime capacity and geographic opportunity

Sea encounters use a commander-and-context simulation, not a mandatory second RTS naval game. Merchants, shipwrights, navigators, crews, geography, ships, weather, and information materially affect operations. Coastal cities gain maritime opportunities; other locations may support exceptional cultural, craft, agricultural, or other districts. Geography enables opportunities; it does not grant free output with no workers or inputs.

## P19 — Time, development, and continuity

Pause and fast-forward make autonomous peaceful development pleasant. Critical events can interrupt speed. General and craft succession operate through simple service/training turnover, not a dynasty RPG. A city, its knowledge traditions, and its political memories persist across decades. Campaign and tactical clocks must have explicit interaction rules.

## P20 — Full-game victory

The desired endgame is recognition as Emperor of Japan through extraordinary military and/or coalition-cultural dominance. This is alternate history, not the ordinary career path of a historical warrior lord. Coalition leadership is an intermediate, comparatively accessible achievement. Imperial victory requires durable legitimacy, recognition, governance, and opposition resolution, not total map painting alone. The regional beta demonstrates coalition leadership, not a misleading national imperial finale.

## Explicit non-goals

No multiplayer, live-service account, runtime AI-text service, naval tactical RTS, modern democracy simulation, thousands of individual character conversations, voxel castle sculpting, or seamless one-to-one Japanese terrain requirement. No claim that a design document or benchmark alone is a beta.
