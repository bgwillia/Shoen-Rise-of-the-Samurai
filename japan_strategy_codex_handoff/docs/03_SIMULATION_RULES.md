# Simulation rules: growth, labor, resilience, and institutions

Everything below is a proposed game model. Coefficients are tuning data, not factual claims about medieval economics. Prefer explicit conservation, readable causality, and bounded effects over a complicated model with untestable realism claims.

## S01 — Population and labor ledger

Home cohorts store `available`, `dependent_or_ineligible`, and `recovering_home` counts. Mobilized people are removed from `available` into the service registry; the home cohort retains a derived `away` display, never a duplicate worker. Service states distinguish mustering, active, wounded_away, captive, missing, deserted_away, and dead. Returned people leave active service and re-enter an appropriate home cohort once. A deserter is not automatically dead or productive: later events may return them, record migration, or leave them missing.

Use this invariant for a closed fixture:

```text
initial people + births + admitted immigrants
= all living home residents + all living people away
  + recorded deaths + recorded emigrants
```

Births and migration have explicit sources. A district becoming wealthy does not generate unaccounted adults. New residents may enter from a finite scenario migration pool or another district, with both ledgers updated. Natural growth alone cannot turn a few hundred people into a huge city over a few years.

Labor available today excludes those away, wounded, captive, dependent, in training full-time, or already assigned elsewhere. A worker cannot operate a forge and harvest rice simultaneously. A training job may allocate part-time work through explicit fractional labor units, never implicit double employment.

Food is consumed at physical location/status: local residents use the home store; an army uses its own supply store. The same deployed person must not consume full rations in both places. Families/dependents still at home continue to eat.

## S02 — Recruitment protects capability unless deliberately overridden

The muster panel shows planned troops, equipment, deployment time, withdrawn workers by occupation/skill, forecasted production, and food reserve impact. Default protections exclude master smiths and other scarce critical workers. An emergency checkbox can override protection after a warning. Recruiting a unit named after a smithing district need not mean recruiting every master there: actual cohort selection is visible.

Honor both district residence and occupation. A household retainer supported by a merchant district is not automatically a merchant removed from a shop. If the soldier really is a working artisan, their absence removes that artisan labor. This distinction prevents the district consequence system from becoming an arbitrary penalty generator.

Casualty attribution uses the actual service record hit/captured/wounded. Never reconstruct casualties by randomly distributing a final count across districts. Report home workforce before mobilization, temporarily absent, dead, recovering, captive/missing, and returned. Avoid counting a death as a second labor withdrawal when the soldier had already left work at muster.

## S03 — Resource accounting

Food is stored in integer person-day units for the beta. Treasury and production resources use integer base units; displays may abbreviate. Every stock follows:

```text
ending stock = starting stock + production + imports + recovered transfers
               - consumption - exports - losses - allocated construction inputs
```

Seed is a protected subaccount of grain, not separate magically edible stock. Releasing seed for food reduces the grain reserved for planting, with an explicit warning. An allocated construction input is removed only once; canceling returns the recoverable part and records the lost part. Spoilage affects stored food with proper bounds, not negative inventory.

Trade reserves the seller's goods at dispatch, creates one cargo record, transfers ownership/payment according to the contract, and arrives or is lost once. No seller can sell the same grain twice while two caravans are en route.

## S04 — Seasonal agriculture and uncertainty

Divide the simulated year into planting, growing, harvest, and off-season phases. Each district has cultivated area, irrigation, soil suitability, available field labor, tool coverage, seed coverage, and a seasonal weather state. Cap planted area by land, seed, and planting labor. Harvest labor caps the share actually gathered.

A simple model is sufficient:

```text
harvest = planted_area * base_yield
          * bounded_weather_factor * irrigation_response
          * crop_health * harvest_labor_coverage
```

Weather emerges through persisted seasonal events in a regional process with local variation. It must not reroll because the camera moved or a save reloaded. Forecasts use observed rainfall/crop condition and scouting/administration quality, not the hidden final yield. Early forecasts are broad ranges; later ones narrow as observations accumulate. A surprise can still occur after a warning, but ordinary play should provide actionable evidence before collapse.

Correlate nearby harvests: otherwise the optimal answer to every local drought is unlimited cheap food next door. Merchants' prices reflect actual available stocks, expected shortage, and transport limits. Do not give an omniscient precise forecast to AI.

UI headline: reserve days at current consumption and a forecast interval under mobilization. Mark confidence and assumptions. Do not display an exact predicted day of famine when uncertain harvest/import outcomes dominate it.

## S05 — Livestock and emergency options

Keep separate species/profile records for breeding adults, juveniles, working animals, age progress, and feed demand; categories must be exclusive or clearly represented as tags without double-counting. Beta can use one generic locally appropriate husbandry profile until species research is complete. Horses have a separate riding/transport ledger and cannot also appear as generic cattle.

Slaughter preview shows immediate food, remaining adults, forecast births, lost work capacity where relevant, and any cultural reaction specified by the scenario. Kill the selected animals once; stop their feed consumption; store usable food subject to storage/perishability. Sustainable husbandry requires time and feed. Buying replacement animals transfers actual stock from an available supplier.

Emergency import, reserve release, demobilization, tax relief, seed consumption, and extraordinary slaughter are real alternatives. Never make every response identical except for a differently named modifier.

## S06 — Organic building decisions

Maintain road graph, buildable parcels, service access, occupation demand, housing demand, and anchor influence caches. Recompute only dirty areas after roads/anchors change. A plot is eligible only when it has access, buildable terrain, funds/materials for development, and demand for its intended use.

Score candidate uses with bounded weighted factors:

```text
score(use, plot) = demand + access + relevant_anchor_support
                  + policy_bias + safety + affordability
                  - terrain_cost - congestion - incompatible_nuisance
```

Reject ineligible candidates first; do not let a giant policy bonus build a warehouse underwater. Choose among remaining useful candidates with a persisted, plot-local random stream. Cap births of new structures per development step and charge real development resources. Empty houses do not imply population; residents arrive through the population model.

Ordinary private development uses local household/merchant investment or an explicit player subsidy. It is not free public construction. The treasury pays for public anchors. Maintenance and service demand remain visible after completion.

Track district character using a moving average of occupied building uses, employment, traffic, and institutional presence. A new dominant label requires sustained change above a threshold, and names/IDs do not flicker monthly. Existing buildings change use only after sustained demand and a real renovation cost. Pinned structures remain untouched. Demolition, relocation, and displacement are distinct commands.

## S07 — Anchors and modules

Each module defines footprint, sockets/attachment rules, construction inputs, build time, required staff, maintenance, local influence, and any settlement-wide effect. An upgrade modifies a particular building instance; it does not globally level every market.

Prefer effects that modify capacity or access: extra storage holds grain; a training court uses instructors and supports a limited number of trainees; a merchant hall improves access to willing trading partners. Additive numerical effects are permitted where transparent, but they cannot substitute for an institution's real prerequisites.

A new road may be required for a module. Reserve construction access and future entrances. Auto manor planning and manual placement call the same validator. A plan with a disconnected gate, inaccessible well, overlapping building, or blocked courtyard is invalid, even when auto-generated.

## S08 — Smithing, equipment, and apprenticeship

A recipe requires a knowledge tag, inputs, workstations, labor by skill, time, and an output quality range. Tool repair competes with weapons. A master can supervise only a bounded number of apprentices and advanced workstations. More low-skill workers increase simple production but do not automatically create elite quality.

```text
batch throughput = minimum(material-limited quantity,
                           fuel-limited quantity,
                           workstation time capacity,
                           qualified labor capacity)
quality band = bounded result of skill, material quality,
               recipe mastery, and chosen inspection effort
```

Do not average one renowned master into a thousand-worker city and magically upgrade every weapon. Track which supervised jobs produced which batch. Quality is stored on equipment and survives trade, capture, issue, and repair. A building's upgrade does not retroactively improve old weapons.

Training accumulates supervised practice. Remove mentor capacity when mentors die, leave, or are conscripted. Retaining masters and supporting apprentices raises capability over multiple years; replacing a destroyed smithing quarter requires facilities and surviving/recruited expertise. The same schema can later serve shipwrights and scholars without implementing every profession now.

## S09 — Elite development

Samurai readiness depends on actual training capacity, retainer support, equipment, mounted resources if applicable, and cultural/martial institutions. Standard formations have shallow experience growth; elites have deeper role mastery and equipment ceilings. No single culture score conjures armored troops with no people or weapons.

Distinguish martial reputation, training level, and equipment quality. A famous but poorly equipped unit is not equivalent to a well-equipped novice or veteran elite. A stable district may sustain an elite tradition of its own, without making forestry residents inherently accurate archers or merchants inherently bad fighters.

Store firearm eligibility as an explicit archetype requirement on an elite training class. It is intentionally a game rule. Discovery still needs an obtainable specimen and production prerequisites. Keep real-world manufacturing chemistry and procedures out of both descriptions and tools.

## S10 — Collective politics and occupation pressures

Track food satisfaction, administrative reach, autonomy, material prosperity, cohesion, and legitimacy separately. Institutions and estates have influence and support. Show a concise status with the top three causes; reveal detailed values only on demand. High policing can reduce immediate disorder while leaving resentment high. Autonomy can improve participation in some conditions and complicate extraction in others; it is not a universal happiness buff.

Warrior approval responds to observed protection, military stewardship, rewards, legitimacy, economic support, and disproportionate losses. It should not automatically punish every strategic retreat or reward senseless attacks as "honor." Diverse content profiles can value these differently without per-samurai dialogue.

Casualty grievance uses actual losses as a fraction of the affected group's deployed and eligible population, recent accumulated burden, support for the war, leadership decisions, and relief to dependents. Casualties always reduce people; grievance is a contextual social consequence, not another source of population loss.

Unrest progresses through warnings, noncooperation, tax shortfalls, desertion, organized opposition, and rebellion. Each requires supporting causes and sustained time, with bounded event probability and a visible response window. Institutions that are protected and provisioned can assist occupation; violated institutions can organize resistance. A religious district has no unconditional surrender bonus.

## S11 — Recovery and anti-snowball rules

Demobilization returns healthy survivors after travel; wounded recover on their own schedules; captives require release/ransom or another outcome. Relief can reduce grievance without resurrecting people. Refugees move between actual ledgers. Destroyed equipment may be partially recovered according to ownership and battlefield control, never assumed completely intact.

Knowledge, housing, imports, surviving mentors, and migration create recovery paths. A defeated player should face difficult choices rather than an unavoidable loop of fewer workers, less food, zero troops, and immediate death after one ordinary defeat. The test suite includes recovery scenarios, not just successful growth.
