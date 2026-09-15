# Actual rendered combat measurements

2026-09-15. Unreal 5.8.2 / CL 56702186, Mac Development editor/game, Metal SM5, Apple M1 Max (10 CPU / 32 GPU cores), 32 GB memory. Actual viewport **1280×720 windowed**; wrapper requests 1600×900. One Unreal process at a time; no builds or heavy tests during captures. F6/F12 off, `t.MaxFPS 0`, VSync off.

Each command starts full opposing armies of ordinary 50-person spear/bow formations, runs actual 20 Hz combat, issues orders to selected formations and moves the camera. Three-second startup warmup precedes a fresh fixture and 45 measured seconds. Numbers of standing soldiers decline with real casualties. All three runs remained in their first battle through the measured interval. No autoresolve, fake casualties or per-soldier Actors.

| Per side | Formations total | Median FPS | Frame median / p95 / worst ms | Simulation CPU p95 / worst ms | Contact ticks | Ranged ticks | Player / enemy casualties | Peak friendly overlap pairs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 500 | 20 | 120.0 | 8.33 / 9.00 / 44.13 | 0.011 / 0.038 | 5,598 | 3,425 | 273 / 243 | 4 |
| 1,000 | 40 | 113.3 | 8.82 / 9.39 / 41.72 | 0.022 / 0.078 | 8,223 | 7,265 | 539 / 408 | 24 |
| 2,000 | 80 | 120.0 | 8.33 / 8.99 / 75.14 | 0.047 / 0.104 | 15,525 | 9,832 | 1005 / 594 | 103 |

Simulation CPU timing covers the domain update inside each rendered game tick. Most render ticks have no fixed 20 Hz combat step, so the near-zero median is not a per-combat-step cost. Portable Release step timings are retained separately and are not rendered FPS. Contact/ranged counters count formation attack ticks; casualty counters count actual killed or wounded soldiers.

The 1,000-per-side run being slightly slower than 2,000 is host/render pacing variation; one short run at each size is not a scaling law. Worst frames of 42–75 ms remain in the results. No input-to-photon or GPU timing is claimed.

## Commands and command usability

- `python3 tools/dev.py combat-benchmark --per-side 500 --seconds 45` — exit 0; 5,376 frames; 23 accepted scripted formation orders; command-batch p95 0.006 ms; peak process memory 3.29 GiB. Raw report: [combat-500.json](combat-500.json).
- `python3 tools/dev.py combat-benchmark --per-side 1000 --seconds 45` — exit 0; 5,093 frames; 27 accepted scripted formation orders; command-batch p95 0.009 ms; peak process memory 3.33 GiB. Raw report: [combat-1000.json](combat-1000.json).
- `python3 tools/dev.py combat-benchmark --per-side 2000 --seconds 45` — exit 0; 5,382 frames; 28 accepted scripted formation orders; command-batch p95 0.010 ms; peak process memory 3.32 GiB. Raw report: [combat-2000.json](combat-2000.json).

The real rendered 240-vs-240 loop demonstrated player advance orders, casualties, routing and return-home effects. The 500/1,000 scale windows were also visually inspected. The 2,000 run was measured with the same rendered path; it finished before a direct visual inspection of that window. No extra run was made merely for screenshot perfection.

Scripted group assignment/selection and order dispatch are measured, not physical command-input latency. Computer-control Ctrl+A and mouse click did not activate their intended actions in the ordinary demo; earlier human physical input acceptance remains distinct.

## Architectural interpretation

No compute or representation limit threatening the core concept appeared at these sizes. The current formation-level algorithm is quadratic in formation count; 80 formations remained cheap here. This does not establish performance with final animation, terrain pathfinding, individual collision, larger armies, other hardware or packaged builds.

The meaningful current weakness is movement quality: only enemy contact standoff exists, with no friendly avoidance, obstacle navigation or congestion resolution. Overlaps rose from 4 to 103 simultaneous friendly pairs. Body ranks and labels can overlap, and routing labels can cross HUD space. This is visible prototype debt, not a solved battle-navigation system. A spatial grid / formation-level local avoidance and terrain corridor planning are plausible next changes if measured bottleneck tests require them; no engine rewrite or one-Actor-per-soldier approach is justified.
