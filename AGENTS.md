# SHŌEN engineering guidance

Read `STATUS.md`, `docs/execution/milestone-1.md`, and the authoritative design package in `japan_strategy_codex_handoff/` before changes. Its `AGENTS.md`, `PLANS.md`, product contract and architecture apply to implementation here. Preserve user-supplied design documents and the asset-production workbook.

The project is in **FEASIBILITY PROTOTYPE MODE** under the user's 2026-09-15 request, `docs/execution/prototype-b-request.md`. Prototype A is accepted at `60ca49fb0416d12423eb8c57ed3e234eba17dedb`. Build Prototype B: constrained terrain, separated formation/group control, representative mixed armies, actual combat measurements and a second mobilization without resetting the settlement. Prioritize playable integration, representative scale and finding architectural limits. Do not split every subsystem into approval milestones; the user explicitly authorizes the integrated work. Targeted accounting/invariant tests, a build, one rendered gameplay demonstration and actual combat scale measurements are required. Exhaustive acceptance, minor UI polish, save migration hardening and platform/packaging work are deferred.

M1, M2A and M2B are accepted. M2C latency measurements and diagnostics are preserved in `docs/execution/milestone-2c-status.md` and `artifacts/latency/`. The user made the slight delay non-blocking; do not optimize it further unless interaction materially worsens. No physical M2C capture has been claimed.

Keep `DomainCore/Public/domain` and `DomainCore/Private/sim` engine-independent. CMake and Unreal must compile the same core. One ledger owns population; presentation may never create or subtract soldiers. Cohorts are aggregated civilians, service records retain immutable origins, and formation membership references service IDs.

Run portable tests and the Unreal build after relevant changes. Report actual launch/visual/benchmark evidence separately. Never claim NullRHI or headless tests measured rendering. Keep generated Unreal and CMake folders out of Git; large binary assets use LFS. Do not stage unrelated pre-existing untracked files.

Run Unreal automation and rendered captures one process at a time in this checkout. Engine instances share the Intermediate asset-registry cache; concurrent writers can create unrelated automation errors. Keep builds and other heavy tests out of latency capture intervals.
