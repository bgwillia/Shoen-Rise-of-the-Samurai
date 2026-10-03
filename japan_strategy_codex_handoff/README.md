# Project Domain — Codex beta handoff

**Working title only. Prepared September 14, 2026.**

This is a design and implementation instruction package, not a compiled game or a claim that any game code has been tested. It converts the approved conversation into a bounded beta and an expansion roadmap. Newly specified numbers, engine choice, region, and thresholds are proposed defaults, not historical statistics or additional user-approved requirements.

## The game in one paragraph

Build a small Japanese manor settlement into an organically growing district-based city. Place its defining buildings and choose their physical expansions; influence the rest through roads, services, resources, and policy. Risk food reserves and skilled labor to equip armies. Command many small formations in large Shogun-style tactical battles. Movement between settlements follows a restricted route network, and generals, scouts, secrecy, and intelligence determine encounter conditions. Soldiers retain district and occupation origins: their actual deaths, injuries, captivity, and desertion change the society that raised them. Samurai are a deeply developed elite and a collective political estate, not a personal-relationship management game.

## How to use this package

Put these contents in a new project root and open that folder in Codex. In an existing repository, put the package under `design-handoff/` first; ask Codex to inspect existing instructions and merge the relevant guidance without replacing files. Paste `CODEX_START_HERE.md` into Codex. It is written to handle either location.

Codex should implement the milestones in order, retaining working builds and evidence between sessions. It should not try to generate the entire finished game in one unreviewable change. The first execution target is M0: a runnable 3D project, deterministic core, and a measured formation-scale test. M0 is not the beta. M9 is the release gate for the complete beta described here.

## Read order

| File | Purpose |
|---|---|
| `AGENTS.md` | Short, persistent constraints for Codex |
| `CODEX_START_HERE.md` | Copy-and-paste implementation prompt |
| `PLANS.md` | Execution and handoff rules |
| `docs/00_PRODUCT_CONTRACT.md` | User requirements, exclusions, and protected design choices |
| `docs/01_BETA_SPEC.md` | Exact beta scope, clocks, campaign, and content |
| `docs/02_ARCHITECTURE.md` | Engine default, data ownership, modules, persistence, scale |
| `docs/03_SIMULATION_RULES.md` | Population, food, organic growth, smithing, and social rules |
| `docs/04_BATTLE_AND_CAMPAIGN.md` | Combat, origin tracking, encounters, occupation, alliances, sea routes |
| `docs/05_INTERFACE_AND_CONTENT.md` | Player screens, controls, visual requirements, content authoring |
| `docs/06_FULL_GAME_ROADMAP.md` | How the beta expands into the intended full game |
| `docs/07_TEST_AND_RELEASE_GATES.md` | Behavioral tests, benchmark protocols, and beta acceptance |
| `docs/08_HISTORICAL_AND_SOURCE_NOTES.md` | Source-backed guardrails and explicit alternate-history choices |
| `docs/09_RISK_AND_DECISIONS.md` | Defaults, risks, and rules against scope drift |
| `docs/10_TRACEABILITY.md` | Feature-to-milestone-to-test map |
| `docs/plans/` | Subsystem implementation plans, including first-task test examples |
| `examples/` | Valid, illustrative JSON contracts and fixtures, not implemented runtime data |
| `templates/` | Status and evidence formats |

## Engine and delivery defaults

Use Unreal Engine 5 with C++ for simulation, input, and testable game rules; use its visual/content tools for presentation. Reuse an existing suitable project instead of switching engines reflexively. Record the installed engine's exact version and platform before generating engine-dependent code. Keep the simulation buildable without the editor using the shared C++ sources and CMake tests described in the architecture.

The beta is single-player, offline, mouse-and-keyboard, and delivered as a packaged desktop build for the machine actually available. Windows is the preferred final target; native macOS builds are acceptable during development when that is the verified host. Do not claim untested platform support. No paid plugin or external account is required by the design.

## What the beta must demonstrate

A real playable loop: build and grow a town; fund master smiths; mobilize identifiable workers; acquire imperfect intelligence; fight a route battle; apply individual service-record outcomes to home districts; respond to labor shortages and political anger; negotiate with neighbors; survive a harvest shock; save and continue.

Smaller scope means fewer regions and content variants, **not** removing organic growth, small formations, elite samurai, or the city/battle consequence loop.

## What completion means

The beta is complete only when the acceptance gates pass on a packaged build with recorded evidence. Full-game completion follows the roadmap's separate gates. Documents, screenshots, a menu mockup, an isolated battle demo, or a headless simulation alone do not satisfy either release definition.
