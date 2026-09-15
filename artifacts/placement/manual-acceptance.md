# Small Storehouse rendered acceptance

2026-09-15; Unreal 5.8.2, Metal SM5, Mac M1 Max, editor `-game`, actual viewport 1280×720. Launch: `python3 tools/dev.py run --scenario settlement`.

## Evidence type

Actions below were performed through the visible native game interface using computer control. They are not headless automation and are not a new human physical-input attestation. The tool can deliver mouse presses at the native pointer but cannot reliably move that pointer. Camera zoom/rotation therefore moved the pointer's terrain intersection during this pass. M1's separately documented human physical-input acceptance remains unchanged. Direct new HUD-button clicks and continuous physical preview movement remain unverified details.

## Complete functional loop

1. B chooses Small Storehouse, shows configured 20 timber/5 treasury cost and green preview.
2. Right bracket rotates 0→15 degrees; rendered footprint/roof follows.
3. Enter places ID 5 at x=1344,y=2647,z=0 cm,yaw=15°; timber200→180,treasury100→95,workers200 unchanged.
4. Repeated Enter over ID5 rejects overlap, red preview/reason, no spend/extra building.
5. Wheel changes ray intersection to another valid point. Native-position mouse press creates ID6 at x=551,y=1957,z=0,yaw=15°; timber160,treasury90.
6. Right-click cancels without resources or an unintended formation order.
7. F5 saves two buildings. B, wheel and Enter create ID7 at x=−268,y=1245,z=0,yaw=0°; timber140,treasury85.
8. F9 removes the unsaved third building and restores two buildings, their orientations/IDs, timber160,treasury90.
9. Paused F5 re-save is byte-identical to step7: 1,194bytes, SHA256 `af13bc225026ddc511a8043106c975c8526cbdb11b375312080c140b5cefeecb`. This also confirms exact full saved state, not only matching labels.
10. Wheel moves preview outside boundary: red reason, Enter rejection. Q camera rotation moves it to the raised 200-permille strip: red steep-terrain reason, Enter rejection. Escape cancels. F5 remains byte-identical to step7.
11. F12 shows matching native/viewport cursor measurements and is turned off for ordinary play.

The functional screenshots retained here can show the intermittent glyph defect. See renderer-isolation.md. The save artifact and manual-save-comparison.txt retain the exact restoration evidence.

## Final ordinary-launch regression

Final original-HUD build and ordinary launch passed the functional replay: F9 restored two records; B/bracket rotated; Enter rejected overlap; wheel reached valid ground; native-position left click added ID7 and debited160/90→140/85; right-click canceled. A final separate F5-save → B/Enter-third-building → F9-load → observed two buildings/160/90 → F5-resave loop was again byte-identical to the original 1,194-byte snapshot. `final-restored-layout.png` records the final state, with F12 off.

One rapid automated F10/F9/F5 batch was rejected as acceptance evidence: both save/load events reached the same game update, whose existing polling order processes F5 before F9. The `.bak` still matched the original two-building fixture; that fixture was restored for a new, separately observed full replay. `final-batched-input.shoen` records the rejected three-building batch result. No save-format failure was observed. Do not batch opposing save/load shortcuts in a single update.

The attempted Slate fallback also reproduced missing glyphs and was removed. Final captures still show intermittent glyph loss, although some frames are complete. No glyph fix or human text acceptance is claimed.
