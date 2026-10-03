I want you to implement the game described in the attached Project Domain handoff. This is authorization to build the scoped beta in stages, not to re-brainstorm the game or create only another design document.

First locate the handoff. It may be in the repository root or under `design-handoff/`. Read its README, AGENTS.md, PLANS.md, product contract, beta specification, architecture, and implementation-plan index. Respect any existing repository instructions and preserve existing work. Inspect the codebase and tools before deciding what must be created.

The game is a fast, readable, 3D Japanese settlement builder starting around 1180, combined with Shogun-style formation battles and simplified city-to-city campaign routes. Its defining feature is that districts produce the actual workers, specialists, samurai, equipment, and soldiers whose losses return to damage those same districts. Civilian simulation is collective; deployed soldiers retain exact origin records. Large armies contain many small formations, not a handful of enormous units. Samurai are the main elite progression system, but not a personal-relationship simulator.

The full design includes organic district growth around manually placed major structures; manual or automatic modular manor construction; uncertain harvests and emergency reserves; master smiths and apprentices; general-driven encounter narratives; merchant/scout intelligence; fragile alliances; society-dependent occupation; artifact-based technical adoption; and maritime capability arising from ports, merchants, and shipwrights. Use the beta versions specified in the handoff. Keep the emperor victory and wider Japan/foreign-contact systems on the full-game roadmap.

For a new repository, use the Unreal Engine 5/C++ default in the architecture. Verify the exact installed engine, compiler, build tools, and target platform. Do not invent tool availability or silently replace this with a web app. If a suitable existing implementation is present, adapt to it and record the mapping from handoff modules/tests to actual paths. If Unreal cannot run in this environment, implement and verify the portable simulation work that is possible, document the exact engine blocker, and do not claim a playable build.

Start with M0. Create a working desktop 3D scene with strategy camera and selection, the shared deterministic simulation module, the portable test runner, and the formation performance test. Use simple original placeholder geometry initially, but the package must launch and the benchmark must measure actual moving/rendered formations. Report the engine/platform, tested commands, measured results, and next milestone. M0 is a technical checkpoint, not the beta.

Then follow the remaining milestones in order across the work sessions needed. At each milestone, create or update an executable plan, write the specified tests, implement the smallest complete behavior, run it, verify it visually when applicable, and update STATUS.md and the evidence log. Do not stop after producing a plan when the environment supports implementation. Do not declare a milestone complete with missing behavior or failing tests. Do not start the full-game expansion while the beta acceptance gates are open.

Important constraints:
- No fake controls, hardcoded demonstration outcomes, or disconnected battle/city state.
- No per-citizen AI and no per-soldier Character/nav-controller architecture.
- No random casualties invented afterward to fit an economy report. Actual soldier service outcomes must drive it.
- No universal "religion makes people obedient" or timeless bushido rule. Use contextual institutional support and interests.
- No free resources for AI, hidden enemy information, duplicate soldiers, instant expert replacement, or future artifacts mislabeled as ordinary 1180 history.
- No paid plugins, online services, runtime LLMs, or copied commercial-game assets required.
- Keep ordinary controls simple and details optional. Reduce content variety before weakening the core loop.

Begin by showing a brief repository/toolchain audit, then implement the first incomplete task. If a prerequisite genuinely blocks progress, identify the specific missing executable/access and preserve a runnable testable result for the next session. Never report a build, playtest, benchmark, or asset verification that was not performed.
