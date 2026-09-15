# SHŌEN engineering guidance

Read `STATUS.md`, `docs/execution/milestone-1.md`, and the authoritative design package in `japan_strategy_codex_handoff/` before changes. Its `AGENTS.md`, `PLANS.md`, product contract and architecture apply to implementation here. Preserve user-supplied design documents and the asset-production workbook.

Current authorization is Milestone 2B building selection and inspection only, recorded in `docs/execution/milestone-2b-request.md` and planned in `docs/execution/milestone-2b-inspection.md`. Milestone 1 is accepted at `44c33ca14de4669031e7e85ab7f157476f5a0a23`. The user physically accepted Milestone 2A game implementation `90d4d1fe9c4275908665d4f00c8159d0aecc6953`; the slight UI delay is a documented, unmeasured follow-up, not permission for speculative fixes. Do not start M2C, production, housing simulation, growth, roads or combat without a new request.

Milestone 2B is now accepted: all requested regressions/build pass, and the user confirmed the complete physical selection/inspection/highlight/placement-transition/save-load checklist on 2026-09-15. See `STATUS.md` and `artifacts/inspection/manual-acceptance.md`. Stop at this accepted slice; a next-milestone recommendation is not authorization to begin it.

Keep `DomainCore/Public/domain` and `DomainCore/Private/sim` engine-independent. CMake and Unreal must compile the same core. One ledger owns population; presentation may never create or subtract soldiers. Cohorts are aggregated civilians, service records retain immutable origins, and formation membership references service IDs.

Run portable tests and the Unreal build after relevant changes. Report actual launch/visual/benchmark evidence separately. Never claim NullRHI or headless tests measured rendering. Keep generated Unreal and CMake folders out of Git; large binary assets use LFS. Do not stage unrelated pre-existing untracked files.
