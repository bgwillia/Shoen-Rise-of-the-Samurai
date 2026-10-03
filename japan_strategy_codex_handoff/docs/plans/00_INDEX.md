# Build order and milestone dependency map

| Milestone | Playable/verifiable result | Plan |
|---|---|---|
| M0 | Runnable engine scene, shared deterministic core, moving formation-scale laboratory | 01_FOUNDATION.md |
| M1 | Direct construction and organic district growth around persistent roads/anchors | 02_CITY_ECONOMY.md |
| M2 | Food risk, labor, reserves, quality/volume smithing, apprentices, elite readiness | 02_CITY_ECONOMY.md |
| M3 | Real tactical battles with many small formations, counterable elites, routing, grouped controls | 03_BATTLE_LEDGER.md |
| M4 | Muster actual workers, fight, apply exact outcomes, recover, save/load | 03_BATTLE_LEDGER.md |
| M5 | Real-map regional campaign, corridor encounters, general narratives, imperfect intelligence | 04_CAMPAIGN_POLITICS.md |
| M6 | Collective politics, fair AI, fragile coalitions, occupation, regional objective | 04_CAMPAIGN_POLITICS.md |
| M7 | Shared manual/auto manor construction and playable assault of saved layout | 05_MANOR_DISCOVERY_SEA.md |
| M8 | Artifact study-to-production, location-specific maritime district and sea encounter | 05_MANOR_DISCOVERY_SEA.md |
| M9 | Complete art/UI/tutorial, hardening, benchmark evidence, packaged playable beta | 06_RELEASE.md |

Sequential ownership: M0 → M1 → M2 → M3 → M4 → M5 → M6 → M7 → M8 → M9. Original art and isolated UI widgets may proceed in parallel once interfaces are stable. Do not split population or battle-result ownership across parallel agents. Later milestones may improve earlier work, but must not replace a core game loop with a mock to claim progress.

Every milestone gets a local executable work plan with actual repository paths. These subsystem plans supply behavior, interfaces, cases, and completion gates; the agent must add implementation-specific line references after inspecting real files. Do not invent file line numbers for an uncreated repository.

The first session should start M0 and reach its strongest verifiable checkpoint. It should not claim to finish this entire index merely because the user supplied a comprehensive prompt. Later sessions resume STATUS.md rather than asking the user to restate the design.
