# Portable DomainCore foundation

CMake and Unreal compile the same three files under `game/Source/DomainCore/Private/sim/`. The portable headers contain no Unreal dependencies; the Unreal module supplies its export macro through the build environment.

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

## Snapshot v1

The disk-independent codec encodes fields explicitly in little-endian order with canonical ordered-map traversal. The 28-byte header contains eight magic bytes (`SHOENM1` followed by zero), a 32-bit version, a 64-bit payload size, and a 64-bit FNV-1a checksum. The checksum detects accidental corruption; it is not authentication.

Payload includes all source counters, resources, general attributes, service origins/statuses, formation role/pose/orders/groups, both clock remainders, RNG state/counters, entity/transaction counters and applied IDs. The format is currently limited to 16 MiB, 100,000 service records and bounded collection/string sizes. Quantities, references, exclusive membership, enums, finite coordinates and conservation are validated before a decoded world replaces the live world. Unsupported versions fail with an explicit error. `EncodeSnapshot` returns empty bytes for an invalid source world.

`LoadSnapshot` performs no file I/O; the Unreal owner handles temporary-file writes and backup/replacement. Saves do not contain pointers, engine objects or executable objects.

## Evidence

`artifacts/core/initial-failures.log` preserves the initial 16 failing behavior suites against API stubs. `progress-failures.log` records 10 passing suites before save/movement implementation. `boundary-failure.log` and `role-failure.log` preserve subsequent failing regression tests before those fixes. `tests.log` and `ctest.log` contain the final current results.
