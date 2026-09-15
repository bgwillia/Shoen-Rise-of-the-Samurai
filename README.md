# SHŌEN — foundation laboratory

Milestone 1 technical prototype for an Unreal strategy/city-building game. See [STATUS.md](STATUS.md) for exactly what has been verified. The authoritative product handoff remains in `japan_strategy_codex_handoff/`; the asset workbook is a separate future production backlog.

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
python3 tools/dev.py run --scenario foundation
```

The map generator creates a real Unreal map and preserves an existing one. The C++ game mode builds the placeholder scene when play begins. You can also open `game/Shoen.uproject` and press Play in the Foundation map.

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

### Mac input diagnosis

F12 shows a red **viewport cursor** and, on macOS, a cyan **native pointer** X. It also displays Slate screen coordinates, the viewport transform, actual pixel resolution, screen backing scale, window DPI, focus and capture state. The native query is read-only; it does not reposition the cursor. Once per second, the same measurements appear as `SHOEN_CURSOR` in the Unreal log.

The computer-control screenshot can display a click marker at a different position from the native macOS pointer. Test physical controls in the actual Unreal application window. Focus the game first, then press Control for group shortcuts. F11 toggles windowed/window-fullscreen mode. The currently measured viewport is 1280×720 windowed; fullscreen follows the display's usable size.

Physical acceptance remains pending; see [STATUS.md](STATUS.md). A keyboard preset is available while diagnosing mouse delivery: Z/X/C/V. No coordinate correction or engine patch is enabled.

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

`game/Saved/SaveGames/Foundation.sav` contains a bounded, versioned, checksummed snapshot. A previous save is kept as `.bak`. Invalid files are rejected before replacing the current simulation. Date, subday remainder, speed, resources, origins, health, formation membership/orders/groups and applied outcome IDs are preserved. Wounded recovery treatment and travel delays are future systems.

## Source layout

- `game/Source/DomainCore/Public/domain/` — plain C++ world, population, formation and snapshot contracts.
- `game/Source/DomainCore/Private/sim/` — shared authoritative implementation.
- `core/` — CMake target and invariant tests compiling those same sources.
- `game/Source/Shoen/` — Unreal subsystem, strategy camera, input, debug HUD and instanced views.
- `tools/` — audited build/test/run wrappers and map generation.
- `docs/execution/milestone-1.md` — scope, decisions and execution checklist.
- `content/provenance/README.md` — placeholder asset provenance.

The next game milestone requires review; development does not automatically proceed to settlement construction or full battles. Check the input-verification status in STATUS.md before treating this prototype as accepted.
