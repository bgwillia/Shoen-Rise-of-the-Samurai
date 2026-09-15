# Human physical-input acceptance — 2026-09-15

Source: the user's direct report in this task, following the diagnostic build at source commit `f8e4c08`.

The user reported:

> I physically tested the current Unreal build.
>
> The F12 diagnostic cursor/cross follows my actual physical mouse pointer correctly throughout the Unreal window.
>
> I also verified that the “1,000 soldiers” UI control responds to a physical mouse click.
>
> I manually tested the current camera and formation controls and did not observe a cursor-position offset.
>
> Treat the previously reported mouse issue as resolved unless another reproducible symptom appears.

The user explicitly requested Milestone 1 acceptance based on the existing automated evidence plus this physical verification, final regression checks, and a final commit. Milestone 2 remains unstarted.

## Evidence scope

- Explicit physical observations: continuous F12-to-pointer agreement throughout the actual Unreal window; successful physical click on the 1,000-soldier control; camera and formation controls tested without an observed cursor offset.
- Camera and formation acceptance is the user's collective attestation. The report does not individually enumerate held-key durations, each drag gesture, each group shortcut, or clicks on the other three presets. Do not represent those as separate measured observations.
- Earlier tool-driven rendering, native-coordinate samples, simulation tests, save/load proofs, and benchmarks provide the complementary evidence recorded in STATUS.md.
- The resolved issue can be reopened if a new reproducible physical-input symptom appears. A displaced computer-control click marker alone is not a physical-input failure.
