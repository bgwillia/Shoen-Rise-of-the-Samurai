# Portable DomainCore foundation

CMake and Unreal compile the same four files under `game/Source/DomainCore/Private/sim/`. The portable headers contain no Unreal dependencies; the Unreal module supplies its export macro through the build environment.

```sh
cmake -S core -B /tmp/shoen-core-build
cmake --build /tmp/shoen-core-build
ctest --test-dir /tmp/shoen-core-build --output-on-failure
/tmp/shoen-core-build/domain_core_tests
```

## Model contract

- `World.h` owns settlements, districts, the six occupation cohorts, resources, generals, immutable service origins, formations, accounting, clocks, and seven independent RNG streams.
- Civilians are aggregate home counts. Mobilization withdraws available workers once and issues new stable service IDs. Healthy and wounded attached services belong to exactly one formation. Dead, captive, missing, and deserted records leave formation membership while remaining in the audit registry.
- `Outcome` requires a unique transaction ID, the current world revision, and exactly one disposition for every current member. Every input is checked before mutation. Wounded soldiers cannot be silently changed back to active by an outcome.
- Demobilization returns healthy people to their exact source cohort's `available` count and wounded people to `recovering_home`. It does not return captives, missing people or deserters. Completed services remain immutable origin/status audit entries; IDs are never reused.
- The closed population invariant is `home + living away + dead + emigrants = initial + births + admitted immigrants`. `Summarize` reports globally or for one origin district.
- Campaign time uses integer microseconds and fixed whole days: three seconds per day at 1×, 360 days per year, starting in 1180. Speed is 0, 1, 3, 5 or 10. Subday remainders persist across speed changes and saves. Daily economy/recovery/birth rules are outside this foundation.
- `Battle.h` supplies laboratory movement at fixed 20 Hz, 600 cm/second; facing is radians. Caller controls whether movement is paused. Slots use local centimeter offsets, 110 cm spacing, ten columns. Group move target centers have 1,500 cm spacing. This is primitive formation locomotion; no combat or pathfinding is implemented.

## Buildings

`Buildings.h` validates oriented rectangular footprints against saved build-area boundaries, existing buildings and the exact triangles of an authoritative height grid. Terrain checks include interior vertices and triangle slopes, not just footprint corners. UI raycasts use the same triangles. Positions use integer centimeters and yaw uses canonical integer degrees; the fixture chooses 15-degree increments through data. Edge touching within 1e-6 cm is allowed.

A successful command atomically commits a candidate world containing one completed building, its stable global entity ID, both resource deductions and its shared transaction ledger entry. Failed commands change nothing, including ID/revision counters. Matching accepted retries return the original ID without spending; conflicting reuse fails. Frozen dimensions and original terrain limits survive tuning changes; saved footprints are revalidated using those frozen limits. Preview evaluation is read-only. Population is untouched.

The current bounded implementation uses pairwise saved-building validation and scans terrain triangles for raycasts; city-scale performance is not certified. Presentation has no per-building Tick.

## Snapshot v2 (v1 migration)

The disk-independent codec encodes fields explicitly in little-endian order with canonical ordered-map traversal. The 28-byte header contains eight magic bytes (`SHOENM1` followed by zero), a 32-bit version, a 64-bit payload size, and a 64-bit FNV-1a checksum. The checksum detects accidental corruption; it is not authentication.

The v2 payload retains the v1 prefix and appends build areas/height arrays and building records. A real accepted-v1 snapshot is committed at `tests/fixtures/milestone1-v1.shoen`; migration leaves buildings/build areas empty and does not initialize a new fixture. New writes are v2; old M1 readers cannot read them.

Payload includes all source counters, resources, general attributes, service origins/statuses, formation role/pose/orders/groups, both clock remainders, RNG state/counters, entity/transaction counters and applied IDs. The format is currently limited to 16 MiB, 100,000 service records, 10,000 buildings, 64 build areas, 65,536 vertices per area and bounded collection/string sizes. Quantities, references, exclusive membership, enums, finite coordinates and conservation are validated before a decoded world replaces the live world. Only versions 1 and 2 are accepted. Unsupported versions fail with an explicit error. `EncodeSnapshot` returns empty bytes for an invalid source world.

`LoadSnapshot` performs no file I/O; the Unreal owner handles temporary-file writes and backup/replacement. Saves do not contain pointers, engine objects or executable objects.

## Evidence

`artifacts/core/initial-failures.log` preserves the initial 16 failing behavior suites against API stubs. `progress-failures.log` records 10 passing suites before save/movement implementation. `boundary-failure.log` and `role-failure.log` preserve subsequent failing regression tests before those fixes. `tests.log` and `ctest.log` contain the final current results.

Placement evidence and 17 behavior suites are in `artifacts/placement/` and `core/tests/test_buildings.cpp`; the original 20 suites remain regression coverage.
