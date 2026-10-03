# Battles, routes, diplomacy, and occupation

## B01 — Tactical unit model

A formation has a stable ID, owning faction, service-record membership, role, command group, equipment summary, frontage/depth, world pose, morale, fatigue, cohesion, ammunition, and orders. Membership can be mixed-origin, but the default recruitment UI groups by district and role to improve readability. Merging/splitting changes membership lists, not soldiers' identities.

Each soldier has a service ID, origin cohort, equipment assignment, health/status, formation membership, and battle slot. Visual entities reference those records. Selecting a soldier may reveal "East Quarter / smith apprentice / ordinary household" without any personal relationship controls.

Ordinary infantry holds space and protects archers. Samurai provide concentrated skill, armor, mounted mobility, and morale strength. Counterplay must include numbers, missiles, frontage, terrain, exhaustion, and exposure. Avoid cartoon immunity to arrows, supernatural area attacks, and stat inflation that renders levies pointless. The intended resemblance to elite fantasy-RTS units is their battlefield importance, not supernatural powers.

## B02 — Orders and AI

Support selection, shift-add, box selection, ctrl-groups, group move, drag frontage/facing, hold, walk/run, attack, charge, fire-at-will, skirmish for missile troops, retreat, and waypoint queues. Many formations can be selected and given one line order with nonoverlapping target frontages. Command groups are UI conveniences; the player can always select a constituent formation.

Formation AI handles its own ranks, target approach, missile range, contact alignment, morale response, and retreat. The enemy battle planner chooses an objective, line, reserve, missile placement, and flanking attempts from what it can see. It cannot read concealed units' exact positions. No individual general character autonomously takes control away from the player's units because of a hidden relationship check.

Separate local combat simulation from animation. A meaningful hit targets an eligible service record in the contact/volley area. Casualty results must respect armor, role, visibility, range, and cover. A melee casualty on a distant untouched reserve indicates a bug, not a plausible abstraction. Slightly abstract contact resolution is acceptable; arbitrary global unit attrition is not.

## B03 — Morale and routing

Morale reacts to casualties, nearby routs, fatigue, flanks, command support, and the operational starting state. Use damped, bounded propagation so a small rout does not automatically delete an entire army. Elites recover or hold longer but can still rout.

Routed soldiers remain alive until actually killed or resolved as missing/captured. Units reaching an escape zone become surviving withdrawals. Pursuit and postbattle outcomes use bounded, explicit rules. End battle when objectives and coherent resistance are resolved; do not demand killing every soldier. Every service ID receives exactly one final disposition.

## B04 — Route model and interception

A route stores endpoints, length in abstract operational distance, ordered sites with normalized progress, travel capacity, terrain, controller/patrol influence, and reports. Armies store route ID and progress. Nodes connect routes; route transitions are explicit.

Before resolving an encounter, compute the space/time window in which opposing forces can interact. Candidate sites must lie inside reachable windows, or require an explicitly simulated delay/withdrawal. A defending army may already control a site. Better command can improve selection or tempo, not ignore geography or distance.

One corridor per directly connected land pair. Supporting armies on the same route are arranged in a convoy/order, not overlapping magical stacks. Capacity and timing matter. Ordinary bypass is disabled in beta; special full-game bypass would need an explicit risky operation rather than a free cursor movement.

## B05 — Resolution and narrative

Resolve an operational sequence: detection, initiative, reachable-site selection, concealment versus counter-scouting, deployment, reinforcement readiness, and withdrawal opportunity. Inputs include general attributes, local familiarity, scouts, spies/stealth support, merchant observations, force size/signature, weather, and supplies. Use saturating weights and bounded random variation. A stronger general should perform better over many trials, not always win or ambush on an open plain.

Store the complete result before opening the battle screen. The result includes `encounter_id`, seed/state, candidate-site audit, chosen site, deployment zones, visibility, surprise, reinforcement schedule, and event reasons. Reloading restores this result rather than rerolling it.

Use deterministic authored sentence templates with fact slots. Example: "Scouts located the opposing column; the commander occupied the reachable western ridge; hostile patrols discovered the flank detachment, preventing a full ambush." Only render clauses whose underlying events happened. Never use a runtime language model or make narration a hidden rules engine.

## B06 — Reinforcements

Arrival requires actual proximity and a viable route. Coordination affects the delay and ordering within a plausible interval, not instant appearance across the map. Reinforcement sides must connect to the army's actual approach. On one corridor, a trailing army cannot suddenly arrive from behind the enemy without a separately established maneuver.

Snapshot schedules on battle entry; show estimates according to intelligence. Direct player control begins when a formation arrives. Do not randomly ignore control orders to portray subordinate incompetence. A failed coordination event may delay arrival but should be warned/explained and statistically bounded. Allied forces use their own service records and consequences.

## B07 — Intelligence and fair AI

An observation contains observing faction, target, source class, observed day, received day, confidence, estimated fields, and expiry/decay policy. Geography/existence knowledge may persist. Economic conditions and force estimates become less reliable with age. A report copied through two intermediaries retains its provenance and becomes less certain, not magically corroborated.

Trade deliveries update general knowledge only along visited/connected routes. Military scouting supplies ranges or rough composition, not inherently exact counts. Spies may reveal sensitive facts at a risk of detection. Captured spies can create diplomatic or occupation grievances; they do not automatically identify every agent network.

Enemy strategy consumes `FactionView`. Difficulty can improve planning budgets or clearly disclosed resource modifiers in a later mode, but beta normal AI has no hidden troop creation or free intelligence.

## B08 — Battle-to-city transaction

Outcome contains one final service disposition per participating person, gear loss/recovery, captured assets, general effects, damage references, ally contributions, and objective result. Validate all records against the encounter's initial roster before applying.

For a fixture with 100 deployed: 10 dead, 15 wounded, 5 captive, and 70 healthy survivors must total 100. At immediate battle completion the 70 remain away until they return; the 15 are alive but unavailable. After return, home available labor increases by 70, not 85 or 100. When five wounded recover, it increases by five. The 10 dead leave the living ledger once. Applying the identical outcome again returns `AlreadyApplied` with no change.

The aftermath UI reports actual occupation-specific effects. Food shortage from absent farmers is not represented as an arbitrary identical penalty to every district. Reducing forge staff must lower the corresponding throughput/capability while unhurt industries remain intact.

## B09 — Conquest and siege

Negotiated surrender, a field defeat followed by surrender, assault, and starvation siege are distinct conquest histories. Store siege duration, disrupted food deliveries, civilian hardship, building damage, combatant losses, broken pledges, and verified covert activity. Do not assume every opposing casualty was a civilian.

On transfer, preserve buildings, districts, their people and crafts, active occupation grievances, and local institutional views. Warrior districts may resist while merchants resume trade. Large settlements require administrative/garrison capacity relative to size and institutional complexity. High honor/legitimacy helps promises be believed; it does not cancel actual suffering. Occupation choices have advertised costs and sustained consequences.

Siege blocks applicable external routes, consumes real reserves, damages legitimacy if promises are broken, and creates an opportunity to negotiate. The basic manor assault uses the actual built compound. Advanced tunneling, siege engines, climb-any-wall systems, and destructible multistory interiors are deferred.

## B10 — Relationships and coalitions

Track trust, directional obligation, shared interests, and recent burden separately. Events have source, target, scale relative to need, day, publicity, and diminishing returns. Providing food during genuine famine can matter far more than repeatedly donating trivial amounts. Ten tiny gifts must not manufacture unlimited obligation. Returning goods in a loop cannot create new reputation each time.

Coalition leadership can be recognized for military ability or for cultural standing, reliability, aid, and negotiated consent. Use a simple nomination/recognition action, not a lengthy constitutional interface. Members retain armies and interests. They can refuse an offensive war, demand relief, renegotiate rewards, withhold forces, or leave after sustained grievance.

Burden uses mobilization duration, actual casualties, material contributions, perceived necessity, reciprocal aid, and reward allocation. Losses are judged in context, not solely by whoever technically controls the formation. Warn before fracture. Do not cause random alliance collapse every few months irrespective of behavior; fragility should be legible and responsive.

## B11 — Maritime simulation

Sea connections contain route length, seasonal risk, coastal knowledge, convoy/escort capacity, and encounter regions. A port's workers, merchant experience, shipwrights, navigation capability, ship condition, and commander combine with weather and intelligence. These inputs affect detection, engagement conditions, escape, cargo delivery, and damage.

Resolve with the same encounter-audit structure, but a naval outcome rather than a mandatory RTS level. Ships have crew records from maritime cohorts, actual cargo, hull condition, and repair needs. Casualties and missing crews return to their home ledgers. A strong merchant district does not give free naval damage; it supplies pilots, information, capital, or capable crews through explicit effects.

## B12 — Later challenges and disputes

The full-game hooks allow a martial demonstration, champion challenge, negotiated arbitration, religious mediation, or pledge-backed settlement. These are optional narrative events with consent/risk, prestige and morale consequences; they do not automatically decide ownership of an entire city through one duel. Research the specific period before presenting a practice as common history. Beta needs ordinary negotiated surrender and event hooks, not a champion combat minigame.
