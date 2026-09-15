# Interaction profiling procedure and boundaries

## Manual capture

Run the Development game with `python3 tools/dev.py run --scenario settlement`. Load the ordinary settlement with F9 if wanted. Keep F12 off to avoid synchronous diagnostic logging. **F6 starts and stops** a bounded capture; the ordinary message line confirms the state. Export is under `game/Saved/Profiling/physical-<UTC>.json`. Profiling is unavailable in Shipping builds.

A useful short pass: click building A, empty ground, A then B; use the visible Build control, move the pointer over terrain, rotate, confirm a valid placement, try an overlapping placement, cancel. Exercise both keyboard and HUD controls. Save/load separately and reselect the restored buildings. Stop capture after roughly a minute; preview polling creates a record each placing frame. Normal gameplay has no profiling overlay or per-event logging. F12 cursor diagnostics remain independent.

The collector holds at most 8,192 actions, 65,536 frame samples, 32 unique stages per action, 64 recent input records and 64 frames of render history. Motion coalesces to its latest sample. Important input eviction and other buffer overflow are counted. An incomplete export must not be presented as a successful end-to-end capture. Stop performs one render drain and disk export outside the sampled action interval.

## Repeatable development scenes

`artifacts/latency/run-captures.py` runs one rendered game at a time, retaining exact argument arrays next to each result. It refuses to overwrite existing captures. For example:

```sh
python3 artifacts/latency/run-captures.py --counts 1 10 100 --iterations 30 --label final
python3 artifacts/latency/run-captures.py --counts 100 --iterations 30 --disabled --label profiling-off
python3 artifacts/latency/run-captures.py --counts 10 --iterations 30 --cap 60 --label cap60
```

The commands use the actual game renderer, not NullRHI. Each scene uses the same flat 13×9 terrain mesh, storehouse catalog, fixed camera and 120 initial warmup frames. Genuine core placement transactions seed 1, 10 or 100 buildings; stocks after seeding are 640 timber and 160 treasury. The camera and actual viewport are unchanged across counts. The raised strip in ordinary settlement content is intentionally absent from these controlled fixtures.

Thirty cycles hold each action for ten frames. Each cycle selects A, clears, prepares A, switches to B (not possible with one building), enters placement, updates the preview, rotates, prepares overlap, rejects overlap, updates to free ground, places successfully, cancels, and restores the baseline. Setup is outside action sampling. Preview refresh also runs between actions while placing; no-point polls are explicitly unevaluated. Correct IDs, phase outcomes, counts and baseline restoration are checked. Cancellation follows the successful placement, so its actual counts are **2/11/101**, not 1/10/100.

The driver calls the existing camera-ray building picker and controller/domain action methods. Its preview points are deterministic world coordinates; this does not exercise physical cursor deprojection. Its samples have `source=replay`. It does not synthesize OS input and cannot report physical-input latency. Companion `.frames.json` files record monotonic wall frame times and outer phase durations with the collector enabled or disabled. Preparatory phases must be excluded from action-cost comparisons.

Fixture ownership is transient and outside World serialization. The session backs up World/catalog/message in memory, prohibits normal save/load/reset/nested fixture use, restores the baseline between cycles and restores the original state on completion. The CLI game then exits. No fixture is written to a normal save slot. Automation verifies both save-file byte preservation and exact restored World/catalog.

## Measured boundaries

- All timing uses `FPlatformTime::Cycles64` and its calibrated seconds-per-cycle value. UTC labels identify files; they do not calculate latency. Domain observers contain no Unreal dependency or clock.
- `slate_constructed_t_ms` is Slate's event-construction timestamp after platform dispatch. `input_receipt_t_ms` is the passive input preprocessor. Controller receipt is recorded separately. The preprocessor always returns false. Recent matching input is consumed once for attribution; stale or unmatched origins remain `frame_poll`.
- `logic_begin`/`logic_end` bracket existing action logic. Named stages identify UI hit handling, picking, stable ID/record lookup, selection changes, preview validation/view work, core validation/copy/commit/resources and deferred presentation rebuild. Duplicate stages are retained once per action. Nested action scopes reuse their parent event. Validation spans can be inclusive; do not add overlapping spans as separate work.
- For successful placement, `transaction_committed` follows the live `World = move(candidate)` operation. Resource changes are authoritative at that same commit. Rejection and idempotent retries do not produce a new commit.
- Applied state is tagged per selection/mode/rotation/preview/buildings/message channel. Scene snapshots use the real main viewport's `FSceneViewFamily::FrameCounter`; HUD snapshots follow the actual draw. Immutable event IDs and per-channel revisions cross to the render thread. Every required channel must match the same frame. Replaced/unmatched states are reported as superseded/pending, never assumed visible.
- `scene_rt_t_ms` is entry to `PreRenderViewFamily_RenderThread`, not completed rendering. The final software endpoint is the same window/frame's **`backbuffer_ready_rt`**, before presentation. It is not GPU completion, compositor delivery or display scanout. A render-frame number identifies the frame's content; it does not mean the CPU and screen finished it simultaneously.
- Repeated selection of the current ID, already-empty clearing and cached/no-point preview polls have no new visual endpoint. Message replacement and unsampled fixture changes invalidate their old visual tokens.

## Analysis

```sh
python3 tools/latency.py capture.json --output report.json
```

The analyzer checks schema, timestamps/frame order, source attribution, drops and incomplete observations. It separates input origins, interaction types, actual building counts and cache outcomes. Each measured interval reports sample count, median, p95 and worst. Input-to-logic is available only for matching Slate samples. Replay totals begin at replay dispatch; frame polls begin at logic entry. Neither is physical switch-to-photon latency.

Software alone does not observe the physical switch, macOS time before Slate construction, GPU completion or screen scanout. A high-speed camera or suitable input/display hardware would be required to measure those omitted endpoints. Current measurements concern the Mac Development editor/game workflow, not a packaged or cross-platform performance certification.
