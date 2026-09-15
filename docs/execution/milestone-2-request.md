Milestone 1 of SHŌEN is accepted at commit:

`44c33ca14de4669031e7e85ab7f157476f5a0a23`

Begin **Milestone 2**, but implement only the first settlement-building slice described below.

Read the current `STATUS.md`, the beta specification, architecture documents, and implementation plan before modifying code.

Do not begin farming, organic district growth, population housing simulation, combat, roads, smith production, or final art yet.

# Goal

Create the first complete, persistent building-placement loop using placeholder art.

The player must be able to:

1. enter building placement mode
2. choose one placeholder building
3. see a placement preview
4. move and rotate it
5. see whether the current footprint is valid
6. see the resource cost
7. confirm placement only if the location and resources are valid
8. have the cost deducted atomically
9. receive a stable building ID
10. save the game
11. reload the game
12. see the building restored in the same location/orientation with the same ID

This is the first real settlement-building foundation for SHŌEN.

---

# 1. Preserve the existing architecture

Do not replace or destabilize the accepted Milestone 1 systems.

Preserve:

* authoritative engine-independent simulation state
* campaign clock
* population ledger
* stable ID approach
* formation performance laboratory
* save/load architecture
* existing automated tests
* F12 diagnostics
* current camera controls

Settlement buildings must follow the same architectural principle:

**simulation state is authoritative; Unreal Actors are presentation.**

A placed Unreal building Actor must not be the sole source of truth that the building exists.

---

# 2. Implement one placeholder building family first

Use a deliberately simple placeholder building.

Recommended first building:

**Small Storehouse**

It does not need real storage gameplay yet.

Its purpose in this slice is to validate the building system.

Suggested initial data:

* Display name: `Small Storehouse`
* Footprint: approximately 8 m × 6 m
* Cost:

  * 20 timber
  * 5 treasury
* Rotation allowed
* Flat-ground placement required
* Cannot overlap another building
* Must remain inside the current settlement buildable area

Treat these as tuning data, not hardcoded assumptions spread throughout gameplay code.

The building definition should live in data/configuration so later buildings can reuse the system.

---

# 3. Building simulation record

Add an authoritative building record with at least:

* stable building ID
* building definition/type ID
* settlement ID
* district ID if applicable
* world position
* rotation
* footprint information or reference to its definition
* construction state
* placement transaction ID if useful
* any versioning fields required by the save format

For this milestone, the building can become constructed immediately after placement.

However, structure the state so later construction phases can be added without rewriting building identity.

Possible future states include:

* planned
* awaiting materials
* under construction
* completed
* damaged
* ruined

Do not implement those systems now unless needed structurally.

---

# 4. Placement preview

Create a building placement mode.

The player should be able to activate it through a temporary/debug building control.

During placement:

* building preview follows terrain under the cursor
* mouse movement updates preview position
* rotation control works
* preview clearly communicates valid vs invalid placement
* footprint is visually understandable
* cancel exits without spending resources
* confirm attempts the placement transaction

Placeholder materials/colors are acceptable.

Do not create final Japanese architecture.

---

# 5. Footprint validation

Implement deterministic footprint validation.

At minimum reject:

### Overlap

The new building footprint intersects an existing placed building.

### Outside buildable settlement area

The building would extend outside the initial allowed settlement boundary.

### Invalid ground

The footprint exceeds the permitted slope/height variation for this first implementation.

### Insufficient resources

The settlement does not have enough required resources.

Keep geometry checks separated from economic checks where practical.

The resulting placement response should provide a reason code such as:

* Valid
* OverlapsBuilding
* OutsideBuildArea
* TerrainTooSteep
* InsufficientResources

The UI may display readable text derived from those codes.

Do not base game logic on parsing UI strings.

---

# 6. Resource transaction must be atomic

Placement is a single transaction.

If the building costs:

* 20 timber
* 5 treasury

then either:

A. the building is created and both costs are deducted

or

B. nothing changes.

There must never be a state where:

* timber is removed but treasury is not
* resources are removed and the building fails to appear
* the building appears but resources remain
* repeated input creates duplicates from one transaction

Use the transaction/invariant philosophy established in Milestone 1.

---

# 7. Stable placement IDs

Every successfully placed building receives a stable unique ID.

Requirements:

* IDs do not change when the view is recreated
* IDs do not change after save/load
* deleting/recreating the Unreal Actor does not create a new simulation building
* failed placement attempts do not create persistent building records
* duplicate confirm input cannot create two buildings from one accepted transaction

Add tests.

---

# 8. Save/load

Extend the existing snapshot format to persist placed buildings.

At minimum preserve:

* building ID
* building type
* settlement ID
* position
* rotation
* completed state
* any data required to recreate its visual representation

Test:

1. place building
2. record ID, transform, and resources
3. save
4. alter the world
5. load
6. verify exact original building state and resource state return

Handle snapshot versioning deliberately.

Do not silently break Milestone 1 saves without documenting the migration/version policy.

---

# 9. Initial settlement fixture

Create a simple settlement-building fixture using the existing placeholder environment.

Give the player enough resources to test multiple placements.

Example:

* timber: 200
* treasury: 100

Display at least:

* Timber
* Treasury
* selected building
* building cost
* placement validity/reason

Keep UI temporary and functional.

Do not redesign the complete game HUD.

---

# 10. Required manual behavior

In the rendered Unreal game I should be able to:

1. enter placement mode
2. select Small Storehouse
3. move its preview around
4. rotate it
5. place it successfully
6. see timber and treasury decrease
7. attempt to place another building on top of it and be rejected
8. move to valid ground and place another
9. move outside the valid settlement area and be rejected
10. cancel placement without spending anything
11. save
12. alter/place additional buildings
13. reload
14. see the saved building layout and resource amounts restored

---

# 11. Automated tests

Add focused tests covering at least:

### Successful placement

Valid footprint + sufficient resources creates exactly one building.

### Resource deduction

Exact configured costs are deducted.

### Insufficient resources

No building created and no resources changed.

### Overlap rejection

Overlapping placement fails without modifying resources or building registry.

### Boundary rejection

Outside-build-area placement fails atomically.

### Stable IDs

Placed building ID persists across view recreation and save/load.

### Duplicate transaction

Repeated placement transaction cannot produce duplicate buildings or duplicate spending.

### Save/load

Building type, ID, transform, and resource state round-trip correctly.

### Determinism

Same initial state + same placement commands produce the same resulting authoritative simulation state where expected.

Run existing Milestone 1 tests as regression tests as well.

---

# 12. Performance and architecture

This does not need procedural cities yet.

However, avoid designing the building system in a way that requires every future ordinary house to have expensive Tick logic.

Buildings should be largely passive unless a gameplay system specifically requires updates.

Future SHŌEN settlements may contain large numbers of ordinary structures, so keep presentation and simulation scalable.

---

# 13. Do not implement yet

Do NOT add:

* residential demand
* organic infill
* district specialization
* roads
* pathfinding
* construction workers
* construction animations
* storage capacity gameplay
* food production
* farming
* smith production
* livestock
* AI city building
* final Japanese buildings
* sound design
* combat
* diplomacy

Those will come later.

This task proves the reusable placement foundation.

---

# 14. Verification

Before reporting completion:

Run all relevant:

* tooling tests
* core simulation tests
* Unreal foundation tests
* new building-placement tests
* Unreal build

Then launch the actual rendered game and manually verify the placement loop.

Do not report placement as working based only on automated tests.

Capture evidence where useful.

---

# 15. STATUS.md

Update `STATUS.md` with:

## Current milestone

Milestone 2 — settlement foundation.

## Implemented

Describe exactly what is working.

## Manual acceptance

List rendered behavior actually exercised.

## Tests

Exact commands/results.

## Save compatibility

Explain snapshot/version changes.

## Placeholder

Explicitly state that the storehouse and interface are temporary.

## Known issues

List actual limitations.

## Next recommended task

Recommend the smallest useful next settlement-building slice.

Do not begin that next task automatically.

---

# Acceptance condition

Stop when one robust placeholder building can be placed through the actual game interface, validated, paid for atomically, assigned a stable authoritative ID, rendered from simulation state, saved, loaded, and rejected safely when invalid.

Commit the verified state.

Then report:

1. final commit
2. files changed
3. architecture added
4. manual tests performed
5. automated tests/build results
6. save-format changes
7. remaining limitations
8. recommended Milestone 2B task

Do not start Milestone 2B.
