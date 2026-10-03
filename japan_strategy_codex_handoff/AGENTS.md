# Project Domain — agent instructions

## Mission

Build the playable beta described in `docs/01_BETA_SPEC.md`, while preserving `docs/00_PRODUCT_CONTRACT.md` and the expansion boundaries in `docs/06_FULL_GAME_ROADMAP.md`. Read those first, then the active plan. This is an offline 3D city-builder/RTS, not a browser dashboard, personal-relationship RPG, or spreadsheet-only simulation.

If this package is nested inside an existing repository, follow existing root instructions and merge guidance deliberately. Preserve unrelated code, assets, and user edits. Inspect the project and installed tools before scaffolding. Never claim an engine, editor integration, plugin, build, or test exists without observing it.

## Protected requirements

- Start small; grow through soft influence and player-placed landmark modules into persistent districts. Keep the original city center and hand-placed structures.
- Aggregate civilian behavior. Preserve exact military service origins: settlement, district, occupation, skill cohort, and estate. No unique civilian-AI character per resident.
- Many small formations, large armies. Do not solve performance by silently turning formations into 800-person units, limiting control to 20 units, or substituting an autoresolve for tactical land battles.
- Samurai are powerful but counterable elite formations and a collective political estate. No individual samurai friendship, marriage, or dialogue simulation.
- Weapon types, quantity, and quality depend on craftspeople, knowledge, materials, and production capacity. Elite gunpowder eligibility is an intentional gameplay rule.
- Fixed city-to-city routes; one land corridor per connected pair; no routine off-route bypass. General encounters must be geographically reachable and explainable.
- Food risk, district losses, alliances, occupation, artifacts, and maritime craftsmanship must produce real state changes, not cosmetic labels.
- Keep the game quick to understand: few routine decisions, useful fast-forward, optional details, no runtime LLM dependency.
- Emperor is the full-game alternate-history victory, not automatically awarded for capturing Kyoto and not replaced with a different title.

## Development rules

Default to Unreal Engine 5/C++ for a fresh project; record exact host/engine/compiler versions. Keep the authoritative simulation in engine-independent C++ using the shared module layout. Use Unreal presentation and its test tooling where needed. Preserve a working existing engine if inspection establishes that it meets the requirements; record that decision before translating the plans.

Use `PLANS.md`. Work on the first incomplete milestone, test it, update `STATUS.md`, and commit a coherent change when a repository permits it. Write failing tests for the named invariants before implementation. Use the systematic-debugging skill when failures are unclear and the verification-before-completion skill before claims of success, where those skills are installed.

Do not create fake `.uasset` files, refer to missing Blueprints, silently install paid assets, scrape game content, or require the user to perform unspecified editor work. Any required editor creation step must be automated through verified engine facilities or documented exactly with its unverified status.

Never use an Actor/Character, skeletal mesh, behavior tree, nav query, or collision sweep for every resident or soldier by default. Formation-level logic and batched representation are the baseline. Profile before deciding on MassEntity or another representation backend.

Use stable IDs, explicit units, bounded randomness, content validation, versioned saves, isolated RNG streams, and a single authoritative owner for each state mutation. Apply battle outcomes transactionally and once only. Do not make AI opponents omniscient.

Claims require evidence: exact command, exit status, report path, build/platform, and visual verification when relevant. A missing tool is BLOCKED, not PASS. Headless success is not evidence of rendering performance. Keep source data provenance and asset licensing records. Never commit credentials or unrelated local files.

## Session output

Report the milestone reached, changed behavior, tests actually run, remaining failures or blockers, launch instructions, and the next executable task. Do not call M0–M8 a completed beta. Do not advance full-game features ahead of the beta's missing gates.
