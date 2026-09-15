> Historical M2C scope: superseded on 2026-09-15 by [feasibility prototype mode](core-loop-prototype-request.md). Preserve results; physical latency acceptance is no longer blocking.

Milestone 2B is accepted at commit:

`396bf5e0f2dd22222edf1a6cbf5bb6c873cfc954`

Begin **Milestone 2C only**.

The purpose of this milestone is to measure and, only if evidence identifies a clear cause, fix the slight UI responsiveness delay reported during physical play.

Do not begin roads, farming, construction simulation, organic growth, final art, or additional gameplay systems yet.

# Goal

Determine where the perceived interaction latency occurs between:

1. physical input
2. Unreal/Slate receiving the event
3. UI hit processing or selection logic
4. authoritative simulation transaction
5. presentation/view-state update
6. rendered visual response

Do not assume the simulation is responsible.

Do not assume Slate is responsible.

Do not optimize without measurements.

---

# 1. Add opt-in interaction latency instrumentation

Add lightweight diagnostics behind a debug toggle.

Normal gameplay should remain clean.

For representative interactions, timestamp the important stages.

At minimum profile:

## Building selection

Measure:

* click/input event received
* building pick initiated
* stable building ID resolved
* authoritative building record resolved
* selection state changed
* inspector/highlight update requested
* next rendered frame containing the new visual state

## Placement

Measure:

* confirm input received
* validation begins
* validation completes
* authoritative transaction committed
* resources updated
* presentation rebuild/update triggered
* placed building first visible

## Placement preview

Measure preview update behavior separately.

Determine whether cursor-following preview is:

* event-driven
* frame-driven
* simulation-day driven
* throttled
* otherwise delayed

A placement preview should not wait for a campaign-day simulation step.

---

# 2. Use a monotonic high-resolution clock

Use an appropriate monotonic timing source.

Do not use:

* simulation calendar time
* system wall clock subject to adjustment
* low-resolution timestamps

Record durations in milliseconds or microseconds as appropriate.

Instrumentation itself must remain lightweight enough not to create the issue being measured.

---

# 3. Measure frame boundary effects

Determine whether the perceived delay is simply one or more rendered frames.

Record where possible:

* game FPS
* frame time
* input receipt frame
* state-update frame
* first frame where updated presentation is visible

At approximately 60 FPS:

one frame is roughly 16.7 ms.

Do not classify normal frame-boundary latency as a defect without evidence.

---

# 4. Look for accidental throttling or polling

Inspect the existing implementation for things such as:

* timers
* delayed delegates
* polling intervals
* Tick interval settings
* campaign simulation callbacks
* unnecessary async work
* selection updates waiting for simulation ticks
* full presentation rebuilds for simple selection changes
* unnecessary save/snapshot work
* repeated world queries
* blocking file operations
* synchronous logging overhead

Do not change any of them unless profiling shows they contribute materially.

---

# 5. Compare several interactions

Collect measurements for at least:

* selecting an existing building
* clearing selection
* switching from building A to B
* entering placement mode
* rotating placement preview
* successful placement
* rejected placement
* canceling placement

Use enough repetitions to distinguish a consistent delay from random frame variation.

Report median and worst observed values where practical.

Do not claim statistical certainty from a tiny sample.

---

# 6. Test with different scene sizes

Use the existing building system to compare approximately:

* 1 placed building
* 10 placed buildings
* 100 placed buildings if inexpensive to generate safely

This is not a dense-settlement performance certification.

It is only intended to answer:

> Does interaction latency increase materially with building count?

Do not manually place 100 structures just for this test if a deterministic development fixture can generate them safely.

Do not persist the fixture into normal gameplay.

---

# 7. Find the root cause before changing behavior

After collecting measurements, identify the slowest meaningful stage.

Write down a specific hypothesis such as:

> "Selection feels delayed because the visual inspector rebuild is deferred until the next frame."

or:

> "The authoritative lookup is fast; the apparent delay is mostly one normal frame plus current editor overhead."

or:

> "Each selection rebuilds all building instances and costs X ms."

Only then consider a fix.

If there is no measurable abnormal delay, do not invent one.

Document that result and leave the architecture unchanged.

---

# 8. If a clear fix is justified

Make the smallest change addressing the measured cause.

Examples of acceptable evidence-driven fixes might include:

* update highlight state without rebuilding unrelated building instances
* remove an unnecessary timer
* decouple placement preview from campaign simulation updates
* cache an ID-to-view lookup if profiling shows repeated expensive searching

These are examples only.

Do not implement them unless measurements support them.

Do not perform broad UI refactors.

---

# 9. Preserve authoritative architecture

Do not make the UI bypass the simulation layer merely to feel faster.

The architecture remains:

input
→ stable entity identity
→ authoritative state/action
→ presentation

Read-only selection presentation may be optimized, but authoritative gameplay transactions remain authoritative.

---

# 10. Regression requirements

After any code change, rerun:

* tooling tests
* core tests
* foundation Unreal tests
* placement tests
* inspection tests
* Unreal build

Add focused tests if the root cause permits meaningful regression coverage.

Then manually verify in the rendered game that:

* building selection still resolves correct IDs
* placement still behaves correctly
* inspector remains aligned/readable
* save/load still preserves buildings
* no interaction was broken by optimization

---

# 11. STATUS.md

Record:

## Measurements

For each tested interaction provide:

* input-to-logic latency
* logic duration
* logic-to-visible-update latency where measurable
* total observed timing

## Scene-size comparison

Record the 1 / 10 / 100 building comparison if completed.

## Root cause

State the actual evidence-supported cause.

If no abnormal cause is found, explicitly say so.

## Changes

Describe any fix made.

If no fix was justified, say that no code behavior was changed.

## Remaining limitations

Include editor overhead and measurement limitations where relevant.

## Recommended next task

After latency investigation is complete, recommend the next actual settlement gameplay slice.

Do not begin it.

---

# Acceptance condition

Milestone 2C is complete when:

* the perceived delay has been measured through the interaction pipeline,
* the dominant source has been identified or the delay has been shown to fall within ordinary frame/update behavior,
* any change made is justified by evidence,
* no regressions were introduced,
* STATUS.md contains the measurements.

Commit the verified state.

Then report:

1. commit hash
2. measured latency breakdown
3. identified root cause
4. whether code changed
5. before/after measurements if fixed
6. regression results
7. recommended next milestone

Do not begin the next milestone.
