# M2C independent code review

Scope: controller/HUD/game-mode integration, transient simulation fixture lifecycle, replay, placement observer use, and the completed interaction collector. Read-only review of implementation; this review did not run builds, games, or tests concurrently with the root worker. Runtime verification is recorded separately in the execution logs.

## Resolved findings

- **P2 — unmeasured replay preparation retained pending visual tokens.** Resolved: disabling sampling now conservatively supersedes and clears all channel tokens; `Invalidate` also operates during capture while sampling is paused. The frame-correlation test includes an unmeasured invalidation case.
- **P2 — rejected-placement message could be replaced before its HUD observation.** Resolved: placement records its expected message, and `CaptureHud` compares the actual displayed message before copying the HUD tokens. The test checks that a replacement message supersedes the rejection.
- **P2 — repeating an unchanged selection fabricated a visible change.** Resolved: controller compares the final resolved selection, marks `selection_unchanged`, and does not replace the Selection token or emit highlight/change stages for the no-op.

- **P2 — input-ring eviction lacked drop accounting.** Resolved: fresh unconsumed non-motion eviction increments `dropped_input_count` and `overflow_count`; mouse motion coalesces to its latest sample. Tests cover 65 click receipts and 100 motion receipts. Final collector/analyzer tests validate the counter.
- **P2 — unevaluated preview labelled as a cache miss (rendered smoke follow-up).** Resolved: preview cache status is null when no evaluation ran, hit when reused and miss only when validation actually began. Tests cover each condition; definitive captures are collected after this correction.

## Remaining findings

None from this scoped review. These changes correct telemetry rather than game latency.

## Verified by source inspection

- Ordinary picking and placement behavior is preserved; replay calls the actual picking, controller placement, and authoritative domain transaction paths.
- Fixture state and content are restored from the original session state. Save, load, reset, and nested-fixture paths are guarded while the transient fixture is active. Core fixture generation uses genuine placements and publishes only a successful candidate.
- Commit and resource markers run after the authoritative candidate replaces World. Rejection and duplicate application do not emit a commit marker.
- Immutable scene and HUD token snapshots carry per-channel revisions. A visual event requires every requested channel to match its event ID and revision within the same frame; scene-dependent events additionally require render-thread observation. A newer game-thread state cannot steal an older snapshot.
- Superseded events may still be observed from an already queued immutable frame that actually contained them; this is correct and differs from matching replacement state.
- Mutable collector events and input state are game-thread owned. Render-frame slots are render-thread owned in production. The bounded observation queue and atomic queue/drop/observing fields connect those threads; callbacks retain or weakly reference the session as appropriate. No demonstrated data race was found in the reviewed paths.
- Session stop unregisters input/draw hooks, removes the view extension, flushes rendering once outside the measured action path, drains observations, exports, and releases the session. Global event IDs and per-session scope serials prevent a retained event ID or scope from aliasing a new capture.
- Input is consumed once; stale input is rejected; replay has explicit source attribution; input callbacks return false and do not consume gameplay input.

## Interpretation and verification limits

`scene_rt_t_ms` is recorded at `PreRenderViewFamily_RenderThread` entry. It means render-thread processing of the matching scene family began; it does not mean GPU completion. The reported endpoint is the matching backbuffer-ready callback on the render thread, not display scanout or physical switch-to-photon latency.

No additional gameplay change or optimization is recommended by this review. Actual rendered correlation, shutdown behavior, and instrumentation overhead still require the separately run Unreal tests and rendered capture evidence.

## Final idle-gating follow-up

Read-only review of the final collector header, implementation, and correlation tests found no new actionable issue in the idle gating. No build, test, or game process was started by this review while the rendered benchmark was running.

- The game-thread gate schedules each required pass while an unobserved event owns the matching channel ID and revision. It does not require both scene and HUD: HUD-only and scene-only requests retain their respective first-observation paths.
- Backbuffer filtering uses the immutable render-frame slot, rather than current game-thread tokens. Retiring or replacing game-thread tokens therefore cannot discard an already queued matching first frame.
- Token retirement occurs only after a full successful frame join. Both event ID and revision must still match before a current token is cleared, preserving newer requests when an older queued frame completes.
- The stored first backbuffer timestamp is protected from duplicate observations. The existing same-frame ID/revision checks still reject stale snapshots and mixed scene/HUD frames.
- Idle render callbacks do not create a slot or queue an empty observation. A scene render marker applies only to a scene snapshot already recorded for that exact frame.
- The reviewed tests cover delayed older completion with newer live tokens, absence of idle work, duplicate endpoint preservation, same-event revision replacement, sampling-disabled invalidation, and HUD-only/scene-only completion. Passing runtime results are owned by the root worker's separate verification evidence; this source review does not substitute for the final rendered baseline.
