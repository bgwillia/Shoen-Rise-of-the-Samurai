# Milestone 1 input acceptance

## Goal

Diagnose the Mac cursor discrepancy at the actual rendered resolution, correct the responsible project layer where possible, and finish physical input acceptance. No Milestone 2 work.

## Architecture

Keep the portable simulation unchanged. Trace the physical macOS cursor, Slate screen cursor, and SceneViewport pixel cursor independently. Diagnostics must observe rather than warp the cursor. Use the engine's geometry transforms instead of empirical scaling.

## Spec

The user's resumed Milestone 1 acceptance request and the open input blocker in STATUS.md. Required physical checks: held WASD, wheel, Q/E, middle rotation, Shift-middle pan, zoom-scaled speed, all preset buttons, hover alignment, individual/box selection, move/facing, multi-formation orders, group assignment/recall/move.

## Progress

- [x] Read status, active plan, input/camera/HUD configuration, and installed Mac/Slate cursor paths.
- [x] Reproduce baseline; instrument independent native and cached coordinates, geometry, DPI, window mode/focus/capture.
- [x] Characterize the automated click-marker discrepancy using independent native coordinates; reproduce separate invalid-click and invalid-box selection failures before changing their behavior.
- [ ] Confirm the original human-click report and continuous physical pointer tracking.
- [x] Apply the smallest evidenced selection fix and review it independently. No coordinate or engine patch.
- [x] Run tooling/core/build/foundation tests (21 tests, CTest 1/1, build success, Unreal 5/5), then relaunch.
- [ ] Complete the human-operated physical input checklist.
- [x] Record exact evidence, limitations, and non-acceptance in STATUS.md.

## Decisions

- Do not modify engine source or apply guessed offsets/scales.
- Computer-control click/keypress events are not evidence of held physical keys or middle dragging. Obtain the user's physical testing observations for those checks.
- Diagnostics are opt-in through the existing F12 toggle and do not affect simulation state.

## Discoveries

UE 5.8.2 Mac mouse-down uses cached cursor state. Normal mouse movement refreshes it from NSEvent.mouseLocation; SceneViewport then converts Slate event coordinates using its geometry and pixel size. The previous synthetic-click mismatch alone does not establish a DPI defect or physical hardware failure. The new native query matches Slate and viewport within one pixel in stable 1280×720 windowed and 1512×949 window-fullscreen samples while the computer-control click marker is elsewhere. Transition-time stale viewport state resolved by the next one-second sample. Physical user observations are still missing.

## Validation

`python3 -m unittest discover -s tools/tests -v`

`python3 tools/dev.py core-test`

`python3 tools/dev.py build`

`python3 tools/dev.py editor-test --suite foundation`

`python3 tools/dev.py run --scenario foundation`

## Handoff

IN_PROGRESS, awaiting the user’s actual mouse/keyboard observations. Automated click delivery is characterized; original physical-click symptoms and the physical acceptance checklist remain open. Final tests/build pass and the rendered game is left open on the 200-worker fixture with F12 enabled. Do not begin Milestone 2.
