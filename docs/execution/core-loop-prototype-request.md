We are changing the current development strategy for SHŌEN.

Until further notice, this project is in **FEASIBILITY PROTOTYPE MODE**, not production-hardening mode.

My current goal is to determine whether the overall game concept is technically and mechanically feasible.

I want substantially faster iteration.

Do not spend an entire milestone polishing, instrumenting, validating, or hardening a small feature unless a failure would prevent us from evaluating the game concept.

The existing foundation work is sufficient for now.

The slight UI latency investigation is no longer a blocking task. Preserve the profiling work and record what is known, but do not spend additional time optimizing it unless interaction becomes materially worse.

# New development philosophy

Prioritize:

1. playable systems
2. representative scale
3. integration between systems
4. discovering architectural limitations
5. determining whether the game is fun

Deprioritize for now:

* exhaustive acceptance testing
* screenshot/evidence perfection
* UI polish
* save migration edge cases
* packaging
* other platforms
* minor visual defects
* extensive instrumentation
* exhaustive automated coverage
* production-quality error handling for prototype-only tools
* polishing placeholder systems

Still perform enough testing to avoid knowingly building on broken foundations.

Do not claim something works without running an appropriate verification, but keep verification proportional to a feasibility prototype.

A smoke test plus a rendered gameplay demonstration is preferable to spending another full milestone proving a small interaction twenty different ways.

# NEXT GOAL: SHŌEN CORE LOOP VERTICAL PROTOTYPE

Build the smallest playable version of the central SHŌEN gameplay loop.

Do not split every small feature into a separate approval milestone.

Work toward one integrated prototype containing the following.

## 1. Small functioning settlement

Create a placeholder settlement containing approximately:

* 500–800 population
* agriculture
* general labor
* smithing
* retainers
* food
* timber
* iron
* basic weapons

Use placeholder buildings.

Provide several basic functional building types such as:

* house
* farm/agricultural area
* granary/storage
* smithy
* manor
* training/retainer area

They do not need final construction animations or finished UI.

The goal is to make the settlement visibly function.

## 2. Simple daily economy

Implement enough economy to demonstrate:

* population consumes food
* agriculture produces food seasonally or through a temporarily simplified production cycle
* workers are required for production
* smiths consume appropriate abstract resources and create basic military equipment
* removing workers reduces economic output

Keep formulas simple and data-driven.

Do not attempt final balancing.

## 3. Mobilization from real population

Allow the player to raise a military force directly from settlement population.

Mobilized people must retain:

* district origin
* occupation
* social/estate origin where already supported

When mobilized they stop contributing normal civilian labor.

Show this visibly in a basic UI.

Example:

Before:
Agriculture workers: 300

Mobilize 100 farmers.

After:
Available agriculture workers: 200
Mobilized agriculture workers: 100

## 4. Equipment

Use a simplified equipment requirement.

For example:

A polearm infantry formation requires:

* people
* basic polearm equipment

Retainer/samurai formations require:

* appropriate population
* better equipment

Use the existing smithing/craft architecture where practical.

Do not implement the final master/apprentice smithing system yet.

We only need to prove that military scale is constrained by civilian production.

## 5. First actual tactical combat

Upgrade the formation laboratory into a crude battle prototype.

Implement enough mechanics to test:

* movement
* formation facing
* contact/melee
* simple ranged attacks
* casualties
* morale
* routing
* basic fatigue
* basic cavalry if inexpensive

Use placeholder soldiers.

Do not implement cinematic combat.

Do not require individual kill animations.

The objective is to test large numbers of relatively small formations.

## 6. Scale tests during actual combat

Test actual combat, not just movement, at escalating scales.

Suggested progression:

* 500 vs 500
* 1,000 vs 1,000
* 2,000 vs 2,000
* higher only if the architecture remains healthy

Measure approximately:

* FPS/frame time
* simulation cost
* obvious pathing/congestion problems
* command usability

We are looking for architectural limits, not release certification.

## 7. Battle resolution feeds back into settlement

This is essential.

After a battle:

* dead soldiers remain dead
* wounded soldiers remain temporarily unavailable
* survivors can return
* occupations remain preserved
* civilian labor changes accordingly

Then allow campaign time to advance.

Demonstrate at least one visible consequence such as:

* reduced agricultural production
* reduced smithing output
* retainer losses affecting available elite troops

This interaction is one of the main feasibility tests for SHŌEN.

## 8. Samurai proof

Add one simple elite samurai/retainer formation.

It should:

* contain fewer soldiers
* require better equipment/resources
* perform substantially better than ordinary troops
* still be vulnerable to poor positioning, exhaustion or overwhelming numbers

Do not implement the final samurai progression system.

We only need to test whether elite units can occupy the battlefield role intended for the full game.

## 9. Fast-forward consequence demonstration

After battle, allow the player to return to the settlement and use time acceleration.

The player should be able to visibly observe that military decisions affected settlement performance.

For example:

Large farmer casualties
→ lower labor availability
→ worse food production

Large smith casualties
→ reduced equipment production

Large retainer casualties
→ fewer elite troops available

## 10. Minimal presentation

Use temporary UI.

I care more about understanding the game than presentation quality.

Provide enough information to see:

* population
* occupations
* food
* basic resources
* equipment
* mobilized population
* army composition
* battle casualties
* post-war economic consequences

Do not redesign the entire HUD.

# What NOT to build yet

Do not spend meaningful time on:

* final Japanese art
* advanced organic district generation
* complete roads system
* religion
* diplomacy
* alliances
* spies
* general encounter narratives
* artifact discovery
* foreign trade
* naval warfare
* advanced castle construction
* detailed livestock
* final historical balancing

Those systems come after the core loop proves itself.

# Validation philosophy

For prototype features:

* write targeted tests for critical accounting/invariants
* run the project build
* perform one real rendered gameplay demonstration
* measure performance where scale matters

Do not create large acceptance matrices for every temporary UI interaction.

Do not block progress over cosmetic issues unless they make the prototype unusable.

# Deliverable

The deliverable is a playable prototype where I can:

1. run a small settlement
2. see its workforce and resources
3. mobilize part of the population
4. see civilian production decline
5. create military formations
6. fight another army
7. suffer real casualties
8. return survivors to the settlement
9. fast-forward time
10. see the economic/social consequence of those losses

This prototype can be visually ugly.

It exists to answer:

**Does SHŌEN's city → army → battle → city loop actually work and feel promising?**

Update `STATUS.md` as work progresses, but do not stop for my approval after every small subsystem.

Stop when this integrated feasibility loop is playable, or when you discover a major architectural limitation that materially threatens the game concept.

If you encounter such a limitation, stop and explain:

* what failed
* at what scale
* measured evidence
* whether an alternative architecture is plausible

Otherwise, complete the integrated prototype and report:

* what is playable
* performance at tested battle sizes
* what remains fake/simplified
* major technical risks discovered
* major design risks discovered
* your assessment of feasibility
* recommended next feasibility prototype
