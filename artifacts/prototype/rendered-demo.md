# Rendered core-loop demonstration

2026-09-15, Unreal 5.8.2 Mac Development editor/game, Metal SM5, actual 1280×720 windowed viewport. Launch: `python3 tools/dev.py run --scenario prototype`.

This was a real rendered gameplay demonstration operated with computer-control keyboard events, not human physical-input acceptance or a headless result.

## Observed loop

1. **N, Space:** fresh paused settlement with 640 living people, 560 available workers and 80 dependents. Farmers 320, laborers 160, smiths 40, retainers 40. Food 3,000; basic gear 250; elite gear 40. Daily food 960 − 640 = **+320**; basic gear **8/day**.
2. **P:** seven campaign days produced food 5,240, basic gear 306 and elite gear 44. Real daily economy ran while preserving the pause setting.
3. **M twice, K, L, J, T:** recruited 100 farmer spears, 50 farmer bows, 50 laborer spears, 20 smith spears and 20 samurai. **240 away**. Ready/away: farmers 170/150, laborers 110/50, smiths 20/20, retainers 20/20. Basic gear 86; elite gear 24. Food production 510, consumption 640, net **−130/day**; basic gear **4/day**.
4. **F, G, Space:** deployed 240 vs 240; issued advance orders to all six player formations; resumed combat. Campaign remained Day 8. Observed blue/red formations moving, contact casualties, bow tracers, shrinking ranks, morale, fatigue, routing, and the smaller elite formation. At **43 simulated seconds: victory**. Player: **157 healthy, 57 dead, 26 wounded**. Enemy: 107 standing, 91 dead, 42 wounded; remaining enemies routed. Samurai retained 15 of 20 while ordinary formations routed.
5. **H, Space:** returned and paused on **Day 9**, after one operational day. 583 living, 477 available, 26 recovering, 57 dead, zero away. Available/recovering: farmers 278/13, laborers 136/8, smiths 28/4, retainers 35/1. Daily food 834 − 583 = +251; basic gear 5/day.
6. **P:** Day 16, 503 available, zero recovering, 57 dead, 583 living. Farmers **291**, laborers **144**, smiths **32**, retainers **36**. Daily food **873** − 583 = +290 and basic gear **6/day**, below prewar production of 960 food and 8 gear. Permanent occupation losses: 29 farmers + 16 laborers + 8 smiths + 4 retainers = **57**.

This completes battle → city → fast-forward consequence in the rendered game. Screenshots accompany this record.

## Input and presentation boundaries

Keyboard recruitment, advance orders, pause/resume, phase changes, returns and fast-forward visibly worked. One automated mouse click and Ctrl+A did not activate their intended actions through the existing computer-control path. No human cursor failure is inferred from that. Prior accepted physical M1/M2A/M2B controls remain the evidence for physical mouse behavior. No new human acceptance gate was requested. Core/group tests and scripted benchmark commands are distinct evidence.

F6/F12 remained off. A small contrast fix to battle/outcome text backgrounds and formation-label shadows followed this first demo. Final rendered combat measurements use that build. Placeholder building labels and overlapping idle army instances in the settlement remain cosmetic simplifications.
