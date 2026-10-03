# M9 — Hardening and packaged beta release Implementation Plan

> For agentic workers: use the installed subagent-driven-development or executing-plans workflow when available. Execute task-by-task with tests and evidence. Do not require unavailable agent tools.

**Goal:** Turn the implemented systems into a tested, readable, complete regional beta that another person can install and play.

**Architecture:** No new flagship systems. Validate the packaged integrated game, its content, sustained state, visual performance, and recovery paths.

**Tech Stack:** Verified Unreal Engine 5/C++, shared engine-independent C++20 simulation, CMake/CTest, Unreal automation, original or licensed content.

**Spec:** `docs/05_INTERFACE_AND_CONTENT.md`, `docs/07_TEST_AND_RELEASE_GATES.md`

## Global constraints

User requirements in `docs/00_PRODUCT_CONTRACT.md` are protected. Exact defaults and limits come from `docs/01_BETA_SPEC.md`. No per-citizen AI, per-soldier Character architecture, personal samurai relationship system, runtime LLM, hidden AI resources, or unverified success claims. Commands below are future wrapper contracts created in M0; their existence is not assumed. New files are proposed paths for a fresh repository; record exact mappings for existing code.

For each task: write the named failing test, run it, implement the behavior, rerun the test and regressions, verify presentation if applicable, update STATUS.md, and commit the coherent change when permitted. Keep the test inputs and expected outputs in the test source, not only in prose. A failed or unavailable gate stays open.

---

## Task 9.1 — Content and provenance audit

**Files:** finalize `content/definitions/`, `content/scenarios/`, `content/provenance/`; engine assets; credits and historical/alternate labels; `KNOWN_ISSUES.md`.

- [ ] Run reference/ID/cycle/geography/era validators over all content. Missing required assets or recipes block release.
- [ ] Complete the twelve anchor families, eight manor module families, five troop roles, four battlefield families, eight nodes, ten land routes, and one sea route.
- [ ] Replace final-beta cubes/statues with readable consistent original or licensed art/animation. Retain cheap development fixtures separately.
- [ ] Audit asset redistribution rights and period fit separately. Do not claim the whole scenario is historically researched while placeholder names/ownership remain.

## Task 9.2 — Onboarding, controls, and human usability

**Files:** introduction scenario, options/input settings, tooltips, event history, UI feedback, campaign and battle menus.

- [ ] Walk a new player through town growth, smith investment, food risk, useful intelligence, recruitment forecast, tactical control, and aftermath.
- [ ] Verify scaleable army selection, remapping, pause, readable overlays, event interruption, UI scaling, and color-independent warning states.
- [ ] Ensure every visible control has functioning behavior. Remove unsupported advertised controls rather than wiring fake success toasts.
- [ ] Play both cautious and risky policies; confirm the interface explains consequences without requiring the debug ledger.

## Task 9.3 — Complete test and soak suite

**Files:** finish T01–T40 cases, property tests, scenario runner, CI where actual tool availability permits; `artifacts/test_reports/`.

- [ ] Run portable and editor suites. Fix failures rather than changing expected values to match bugs.
- [ ] Run at least ten 20-year campaign simulations with distinct fixed seeds, conservation checks, bounded stocks, AI survival, and save/load interruptions.
- [ ] Play costly victory, recoverable defeat, fragile alliance, occupation, artifact, sea-loss, and manor assault scenarios.
- [ ] Test corrupted saves, unsupported content version, midbattle restore, duplicate result application, rapid command cancel, and view switching under fast-forward.

```sh
python tools/dev.py core-test --all
python tools/dev.py editor-test --all
python tools/dev.py run --scenario beta_region
```

Record actual tests/results rather than assuming every suite succeeded because compilation did.

## Task 9.4 — Packaged performance and platform verification

**Files:** benchmark scenarios/wrappers, reports, build settings, release candidate artifact.

- [ ] Package a release candidate on the available supported platform. Launch that packaged binary, not only play-in-editor.
- [ ] Run the city fixture and 8,000-soldier contact fixture with real art and UI using the performance protocol. Separately report the 20,000 stress result.
- [ ] Profile and fix frame spikes, selection latency, render costs, retained actors, and formation deadlocks. Do not lower formation count by silently enlarging units.
- [ ] Record tested hardware and settings; make no unsupported cross-platform or weaker-GPU claims.

```sh
python tools/dev.py package --configuration Development
python tools/dev.py benchmark --scenario beta_battle --soldiers 8000 --seconds 120 --mode combat --packaged
python tools/dev.py benchmark --scenario scale_lab --soldiers 20000 --seconds 120 --mode combat --packaged
```

Actual packaging configuration may change after inspection; record the exact engine command and artifact location.

## Task 9.5 — Acceptance report and beta tag

**Files:** release notes, launch/install instructions, `STATUS.md`, final report, `KNOWN_ISSUES.md`, credits; release tag when source control is available.

- [ ] Complete both regional military and coalition victory playthroughs and a post-victory sandbox continuation.
- [ ] Check every traceability entry against working packaged behavior. No core data-loss, duplicate-population, broken-progression, or severe pathing issue may be left open.
- [ ] Publish the tested artifact path, exact build ID, platform, test evidence, performance results, known limitations, and instructions to reproduce the key scenarios.
- [ ] Mark M9 VERIFIED only after the complete gate passes. Otherwise report an alpha/partial beta accurately and list the exact unmet gates.

**M9 exit:** another player can launch, learn, grow, fight, suffer consequences, recover, negotiate, win, save, reload, and continue in the actual packaged game. Only then begin the full-game roadmap.
