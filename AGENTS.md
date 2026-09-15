# SHŌEN engineering guidance

Read `STATUS.md`, `docs/execution/milestone-1.md`, and the authoritative design package in `japan_strategy_codex_handoff/` before changes. Its `AGENTS.md`, `PLANS.md`, product contract and architecture apply to implementation here. Preserve user-supplied design documents and the asset-production workbook.

Current authorization is the user's first technical milestone only. Do not continue into settlement-building M1 from the handoff without a new request.

Keep `DomainCore/Public/domain` and `DomainCore/Private/sim` engine-independent. CMake and Unreal must compile the same core. One ledger owns population; presentation may never create or subtract soldiers. Cohorts are aggregated civilians, service records retain immutable origins, and formation membership references service IDs.

Run portable tests and the Unreal build after relevant changes. Report actual launch/visual/benchmark evidence separately. Never claim NullRHI or headless tests measured rendering. Keep generated Unreal and CMake folders out of Git; large binary assets use LFS. Do not stage unrelated pre-existing untracked files.
