# Milestone 2A UI/input latency follow-up

## Status

OPEN known issue; **Milestone 2A remains physically accepted**. On 2026-09-15 the user reported a small but perceptible delay in UI response in the actual Unreal game, with no missed inputs or incorrect interaction. The user confirmed correct HUD text, preview tracking, controls and placement/save behavior.

Game implementation: `90d4d1fe9c4275908665d4f00c8159d0aecc6953`. No quantitative latency measurement, distribution, stage attribution or cause is established. Do not treat the earlier automated capture anomalies or rapid shortcut-batch observation as a measured cause of this physical delay.

## Current instrumentation and decision

F12 remains off by default. While enabled, the existing controller logs `SHOEN_INPUT` for left-button events and `SHOEN_CLICK` for polled clicks; `SHOEN_CURSOR` records periodic native/Slate/viewport state. F12 off stops these project diagnostics. These are timestamped diagnostic logs, not an event-to-present timing trace.

The controller receives input after earlier platform/Slate dispatch. HUD drawing records work before the actual displayed result. Adding isolated timestamps at those two functions would leave both ends of the requested measurement unobserved. Reliable correlation across the five stages below needs platform/Slate and presentation hooks, clock alignment and verification. That is deferred to a focused profiling pass instead of expanding this documentation-only acceptance commit. No new instrumentation or speculative fix is implemented.

## Measurement boundaries for a future opt-in pass

| Stage | Measurement point | Interpretation and limit |
|---|---|---|
| Physical input event receipt | Earliest available platform/Slate mouse event timestamp, correlated to `AFoundationPlayerController::InputKey` | Distinguishes dispatch delay from later work. Controller entry alone is not OS receipt or physical button activation. Cursor-position polling is not an event timestamp. |
| UI hit processing | Entry/exit of `AFoundationHUD::NotifyHitBoxClick`, hitbox ID and originating event ID | Separates UI routing from the command. A world click can bypass a HUD hit; do not assume every event passes this stage. |
| Placement-preview update | `UpdatePlacement` / `RefreshPlacement` and completion of `ASettlementView::SetPreview`, tagged with preview pose/version and game frame | Separates cursor sampling, validation and presentation-data update. Updating a component does not prove its pixels were presented. |
| Simulation transaction | Around `UShoenSimulationSubsystem::PlaceBuilding` / `domain::PlaceBuilding`, with transaction ID, result, world revision and view generation | Measures authoritative work and connects an accepted transaction to `AFoundationGameMode::RebuildViews`. Preview/cancel may produce no transaction. |
| Rendered response | Correlate updated preview/view generation and HUD frame with render-thread/GPU submission and presentation timing | `DrawHUD`, component update and backbuffer readiness are intermediate events, not proof of display scan-out. Report the available boundary accurately; physical input-to-photon measurement requires external observation. |

Use correlated event IDs and game/render frame IDs, with monotonic CPU timing and validated cross-clock conversion for OS/GPU timestamps. Separate click response from continuous-preview tracking and avoid mixing events from different commands or replacement worlds.

## Constraints for that profiling pass

- Explicit development-only capture option, disabled by default; keep ordinary play quiet.
- Bounded trace/buffer output, with measurement overhead checked. No per-event console or permanent on-screen spam.
- No simulation/save/input-behavior changes to obtain measurements.
- Record actual viewport, display mode, frame pacing, workload, build and whether diagnostics were enabled.
- Compare capture-enabled and ordinary play before attributing a delay. Do not infer a fix from average FPS alone.
- Only propose a latency change once the responsible interval is measured. Rerun relevant regressions and physical checks if runtime code changes.

These are future measurement notes, not implemented telemetry or measured results. They do not authorize Milestone 2B work or speculative latency fixes.
