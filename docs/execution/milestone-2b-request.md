Milestone 2A, the first persistent building-placement slice, is accepted.

Begin **Milestone 2B only**.

Read the latest `STATUS.md`, current implementation, beta specification, and relevant architecture documents before modifying code.

Do not begin roads, farming, organic growth, construction workers, smith production, housing simulation, or final art yet.

# Goal

Implement a reusable building-selection and inspection system.

The player must be able to physically click a placed Small Storehouse and inspect the authoritative simulation record that produced it.

This is not merely a tooltip exercise. The purpose is to establish the interaction architecture later used by manor buildings, smithies, markets, temples, warehouses, defenses, districts, and other simulation entities.

---

# 1. Preserve simulation authority

The Unreal visual representation must not become the source of truth.

Selection should resolve:

visual representation
→ stable building ID
→ authoritative simulation building record
→ inspection presentation

Do not duplicate authoritative gameplay values inside the Unreal Actor merely for UI convenience.

If the view Actor/instance is recreated, the same building must still resolve to the same simulation record.

---

# 2. Physical building selection

Allow the player to click an already placed building in the normal settlement view.

Requirements:

* click building → select it
* selected building gets a simple visible highlight
* click empty terrain → clear selection
* selecting another building changes selection
* entering placement mode clears or safely suspends ordinary building selection
* leaving placement mode restores normal selection behavior
* save/load and visual reconstruction do not break click-to-ID mapping

Use placeholder highlighting.

Do not create final selection effects.

---

# 3. Inspection panel

Display a temporary inspection panel for the selected building.

For the Small Storehouse show at least:

* Display name
* Stable building ID
* Building definition/type ID
* Settlement ID
* District ID, if assigned
* Position
* Rotation
* Footprint dimensions
* Construction/completed state
* configured build cost

Clearly distinguish:

### Instance information

Information belonging to this specific placed building:

* stable ID
* transform
* state
* settlement/district

from:

### Definition information

Information belonging to the building type:

* display name
* footprint
* configured cost

This distinction will matter later when individual buildings become damaged, upgraded, occupied, or specialized.

---

# 4. Stable selection identity

Selection should be based on stable simulation IDs.

Do not use:

* display name
* Actor pointer identity
* array index
* temporary instance ordering

as the persistent identity of a building.

If presentation is rebuilt, the selected building should either:

A. safely reacquire the same ID,

or

B. clear selection intentionally if the relevant world state no longer contains that ID.

Never silently select a different building because an array changed order.

---

# 5. Save/load behavior

Test this sequence:

1. Place at least two storehouses.
2. Verify they have different stable IDs.
3. Select one.
4. Record its ID and transform.
5. Save.
6. Alter the world.
7. Load.
8. Select the corresponding restored building.
9. Verify the same ID, type and transform appear.

Persistent selection across save/load itself is optional for this slice.

Persistent **building identity** is mandatory.

Do not expand snapshot scope solely to save UI selection unless there is a clear architectural reason.

---

# 6. Multiple-building proof

Place several storehouses.

Verify that clicking each visual building resolves to the correct authoritative building.

This test is important because future settlements may contain thousands of structures.

No lookup may depend on "first building" or equivalent fixture assumptions.

---

# 7. Architecture for future entity inspection

Keep the building panel focused, but design the selection interface so future simulation objects can use the same general concept.

Future examples include:

* district
* formation
* major building
* manor module
* resource facility

Do NOT implement a giant generalized reflection/UI framework now.

Create only the smallest useful abstraction necessary to prevent building selection from being hardcoded into an unextendable one-off system.

---

# 8. Automated tests

Add focused tests where appropriate for:

* unique IDs across multiple placed buildings
* correct ID-to-building lookup
* lookup remains correct after snapshot round-trip
* removal/missing ID fails safely
* presentation recreation does not mutate simulation identity
* selecting one building cannot resolve the data belonging to another

Preserve and rerun all existing population, save, formation, and placement regression tests.

---

# 9. Manual acceptance

In the actual rendered game verify:

1. Place three storehouses in different positions/rotations.
2. Exit placement mode.
3. Click storehouse A.
4. Confirm its highlight and inspection information.
5. Click B and verify ID/transform change.
6. Click C and verify again.
7. Click empty terrain and confirm deselection.
8. Save.
9. Alter the world.
10. Reload.
11. Click the restored buildings and verify their authoritative IDs and transforms.

Physically use the mouse for this acceptance pass.

---

# 10. Scope exclusions

Do NOT add yet:

* demolition
* building upgrades
* construction queues
* workers
* inventories
* storage capacity
* roads
* farming
* residential development
* organic infill
* district specialization
* smith production
* advanced HUD redesign
* final art

We are proving reusable object interaction first.

---

# 11. Verification and status

Run:

* tooling tests
* core simulation tests
* placement tests
* new selection/inspection tests
* Unreal foundation tests
* Unreal build

Then perform rendered manual verification.

Update `STATUS.md` with:

* M2B status
* architecture added
* exact physical interactions verified
* automated test/build results
* placeholder UI limitations
* known issues
* recommended M2C task

Commit the verified state.

Stop after Milestone 2B.

Do not begin M2C automatically.
