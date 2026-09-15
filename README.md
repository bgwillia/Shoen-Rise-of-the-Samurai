# SHŌEN — settlement foundation

Milestone 1 is accepted. Milestone 2 adds the first persistent Small Storehouse placement slice for the Unreal strategy/city-building prototype. See [STATUS.md](STATUS.md) for exactly what has been verified. The authoritative product handoff remains in `japan_strategy_codex_handoff/`; the asset workbook is a separate future production backlog.

## Run on this Mac

Requires Unreal 5.8.2, Xcode with Metal Toolchain, Python 3, CMake and Git LFS. The verified engine installation is `/Users/Shared/Epic Games/UE_5.8`. Set `UE_ROOT` or pass `--engine` to use another compatible installation. Other platforms are unverified.

```sh
git lfs install --local
git lfs pull
python3 tools/dev.py doctor
python3 tools/dev.py core-test
python3 tools/dev.py build
python3 tools/dev.py create-map
python3 tools/dev.py editor-test --suite foundation
python3 tools/dev.py editor-test --suite placement
python3 tools/dev.py run --scenario settlement
```

The map generator creates a real Unreal map and preserves an existing one. The C++ game mode builds the placeholder scene when play begins. You can also open `game/Shoen.uproject` and press Play in the Foundation map.

## Small Storehouse placement

Launch `python3 tools/dev.py run --scenario settlement`, or press **N** / **New settlement fixture** in the existing lab. The fixture starts with 200 timber, 100 treasury and the same 200 workers. New-fixture controls replace the unsaved test world.

Choose **Small Storehouse** (B), point at ground, rotate with **[ / ]**, and **left click / Enter** to build. Green means valid; red shows a typed rejection reason in the HUD. The 8×6 m placeholder costs 20 timber and 5 treasury, completes immediately, and creates no population. Costs/dimensions/tolerances come from `game/Content/Domain/Data/buildings.json`.

The gold outline bounds the build area. The raised strip is deliberately too steep. Overlap, a footprint beyond the boundary, invalid terrain, or insufficient resources rejects the whole transaction. Exact footprint edge contact is allowed. **Esc / right click** cancels without spending. Preview freezes over the HUD so its rotate/confirm buttons act on the last ground location. Camera controls remain available; formation selection/orders are suspended only during placement.

F5 saves the layout, resources and stable IDs. Place more, then F9 restores the saved state. The HUD shows the last building ID. N starts a fresh fixture; R returns to the accepted population lab. Buildings are passive instanced presentation of authoritative simulation records; no storage, production, construction-worker or housing gameplay exists.

## Controls

| Action | Control |
|---|---|
| Pan | WASD |
| Zoom | Mouse wheel |
| Rotate | Middle-drag or Q/E |
| Drag pan | Shift + middle-drag |
| Select formations | Left click or drag a box; Shift adds |
| Move | Right click destination |
| Move with facing | Right-drag from destination toward facing |
| Group | Ctrl+1–9 assigns; 1–9 recalls; Ctrl+A selects all |
| Pause / resume | Space |
| Speed 1× / 3× / 5× / 10× | F1 / F2 / F3 / F4 or buttons |
| Save / load | F5 / F9 or buttons |
| Capture screenshot | F10, saved under `game/Saved/Screenshots/` |
| Clear selection | Escape |
| New 1k / 4k / 8k / 20k fixture | Z / X / C / V |
| Reset to 200-worker proof | R |
| Toggle cursor diagnostic | F12 |
| New settlement fixture | N or top-right button |
| Choose / toggle building placement | B or Small Storehouse button |
| Rotate building | [ / ] or placement buttons |
| Confirm / cancel building | Left click or Enter / right click or Esc |

### Mac input diagnosis

Diagnostics are **off by default** during ordinary play. F12 toggles a red **viewport cursor** and, on macOS, a cyan **native pointer** X. It also displays Slate screen coordinates, the viewport transform, actual pixel resolution, screen backing scale, window DPI, focus and capture state. The native query is read-only; it does not reposition the cursor. While enabled, the same measurements appear once per second as `SHOEN_CURSOR` in the Unreal log; toggling F12 off also stops this logging.

The computer-control screenshot can display a click marker at a different position from the native macOS pointer. Test physical controls in the actual Unreal application window. Focus the game first, then press Control for group shortcuts. F11 toggles windowed/window-fullscreen mode. The currently measured viewport is 1280×720 windowed; fullscreen follows the display's usable size.

The user physically verified pointer alignment, the 1,000-soldier button, and camera/formation controls. Milestone 1 is accepted; see [STATUS.md](STATUS.md). Z/X/C/V remain the preset shortcuts. No coordinate correction or engine patch is enabled.

Automated captures intermittently show missing sections of HUD letters in the settlement scene. The placement/save loop is verified, but physical confirmation of this text symptom is pending. No speculative renderer override is enabled; see STATUS.md and the renderer investigation for the remaining visual limitation.

### Population proof

Choose **Reset: 200 workers**, **Mobilize 100**, **Apply 20/15/65**, then **Return survivors**. The ledger must show **165 available, 15 wounded at home, 20 dead**. This is a labeled scripted accounting proof. It is not tactical combat. M mobilizes, O applies the fixture outcome, and Backspace demobilizes.

### Scale laboratory

The four buttons start new, finite source-population fixtures with 1,000 / 4,000 / 8,000 / 20,000 soldiers in 100-person formations. Reset replaces the current unsaved test scenario. Every rendered soldier references a mobilized service record. One formation Actor contains one instanced-mesh component; individual soldiers are not Actors.

```sh
python3 tools/dev.py benchmark --soldiers 8000 --seconds 120
python3 tools/dev.py benchmark --soldiers 20000 --seconds 120
```

Benchmarks warm up for 10 seconds, move formations, change selection, pan/zoom the camera, and write actual frame-time and memory reports under `artifacts/`. These are primitive movement measurements. No combat, soldier animation, terrain navigation, final art, or shipped scale is implied.

## Save files

The laboratory uses `game/Saved/SaveGames/Foundation.sav`; settlement mode uses `Settlement.sav` in the same directory. Each slot retains its previous save as `.bak`. Temporary writes and validation precede replacement.

**Writer v2; reader v1 and v2.** Actual Milestone 1 v1 snapshots migrate with their exact population, formation, clock and resource state, and empty building/build-area registries. Migration does not invent a settlement fixture. All new saves use v2; the old M1 executable cannot read them, so retain original v1 files when using that executable.

V2 additionally preserves terrain, building IDs/type versions, position, yaw, frozen dimensions, completed state and placement transaction IDs. Reloading never reapplies costs or resizes old buildings from changed tuning. Missing building types or a save requiring a newer definition version reject the load while preserving the current world. Definitions are loaded from content; saved terrain/resources are independent of the new-fixture file. Invalid/unsupported snapshots fail explicitly. The checksum detects corruption, not malicious tampering.

## Source layout

- `game/Source/DomainCore/Public/domain/` — plain C++ world, population, formation, building-placement and snapshot contracts.
- `game/Source/DomainCore/Private/sim/` — shared authoritative implementation.
- `core/` — CMake target and invariant tests compiling those same sources.
- `game/Source/Shoen/` — Unreal subsystem, strategy camera, input, debug HUD and instanced views.
- `tools/` — audited build/test/run wrappers and map generation.
- `docs/execution/milestone-1.md` and `milestone-2-placement.md` — scope, decisions and execution checklists.
- `content/provenance/README.md` — placeholder asset provenance.

This slice stops at persistent placement. Milestone 2B requires a new instruction; see STATUS.md for acceptance evidence and limitations.
