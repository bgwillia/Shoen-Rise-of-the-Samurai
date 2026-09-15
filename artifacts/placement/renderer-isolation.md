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

## Conclusion and remaining issue

Intermittent missing HUD glyph sections are visible in automated captures of the actual Metal game. Some frames are complete; some are not. This investigation has not isolated a specific project, engine, driver or capture-path cause. A new human physical check of whether text visibly flickers/disappears was requested; no answer is recorded at completion.

The functional placement loop, resource transactions and save restoration are independently verified. The final project retains the original Canvas HUD and passive building ISM batches, plus the existing F12 diagnostics. Ineffective renderer overrides, diagnostic launch flags and the failed Slate overlay are absent. No engine patch, global CVar policy or pointer correction was added.

This remains a visual acceptance limitation, not a claimed fix. Inspect the physical Unreal window before treating the text presentation as fully accepted. If physically reproducible, investigate the rendering path before expanding the interface. Existing screenshots are functional-state evidence and may contain the symptom.
