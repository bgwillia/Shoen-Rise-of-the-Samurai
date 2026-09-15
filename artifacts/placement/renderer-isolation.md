# Mac rendered HUD investigation

UE 5.8.2 / Metal SM5 / Mac M1 Max / 1280×720. Actual rendered observations, 2026-09-15.

## Reproduction and isolation

1. Empty settlement: complete Canvas HUD text. Load two placed buildings with F9: intermittent missing triangles/sections of Canvas glyphs. The saved world, resources and building geometry remain intact. Engine F10 captures also contain the defect; it is not just the computer-control screenshot.
2. Temporarily omit only custom roof instances while retaining builtin cube bodies, terrain, HUD and the same saved world: corruption remains. This rules out custom roof geometry as a necessary cause. Roof rendering was restored after this experiment.
3. `ShowFlag.InstancedStaticMeshes 0` produced a clean comparison frame with the same world/HUD. The symptom correlates with the scene's instanced drawing workload.
4. `r.MeshDrawCommands.DynamicInstancing 0` initially appeared to fix the body-only scene. Further full-scene and preview observations reproduced corrupt text at value 0. Clean isolated frames were insufficient evidence. This attempted project override and its lifecycle test were removed.
5. `r.MeshDrawCommands.UseCachedCommands 0` also reproduced corrupt text. No cached-command override is retained.
6. Fresh launches with `-MetalRuntimeDebugLevel=2` (reset resource bindings on pipeline changes) and `=5` (also wait for command-buffer completion) still reproduced the symptom with automatic instancing enabled. These diagnostic launch flags are not ordinary-play configuration.

Independent installed-source review found Canvas disables depth tests and preserves batch order. Canvas and Metal explicitly supply instance count, base instance and vertex offset on each indexed draw. Fast runtime mesh creation copies the mesh-description data into owned buffers; no dangling description lifetime was found. No particular engine/driver line is established as the root cause.

7. A temporary settlement-only Slate text overlay reproduced the same missing glyph sections during extended interaction. It was removed; this is not established as Canvas-only.
8. With all ISM drawing hidden, several changing preview frames were clean, but enabling F12 with the static preview visible reproduced missing text again. Explicit building instancing is therefore not a necessary cause. No speculative change to the batch backend is retained.

## Historical conclusion before human acceptance

Intermittent missing HUD glyph sections are visible in automated captures of the actual Metal game. Some frames are complete; some are not. This investigation has not isolated a specific project, engine, driver or capture-path cause. At the implementation commit, a human physical check was still pending.

The functional placement loop, resource transactions and save restoration are independently verified. The final project retains the original Canvas HUD and passive building ISM batches, plus the existing F12 diagnostics. Ineffective renderer overrides, diagnostic launch flags and the failed Slate overlay are absent. No engine patch, global CVar policy or pointer correction was added.

At that point this was a visual acceptance limitation, not a claimed fix. Existing screenshots preserve the observed capture symptom.

## Human acceptance update — 2026-09-15

The user physically verified the actual game and confirms that HUD text renders correctly, the preview follows the physical mouse, the new controls respond correctly, and placement/rotation/validation/cancellation/save-load appear correct. Milestone 2A is explicitly accepted. The earlier capture anomaly no longer qualifies acceptance; its underlying cause is not established, and no renderer fix is claimed. A slight UI response delay, without missed inputs or incorrect behavior, is tracked separately in STATUS.md and the latency profiling notes.
