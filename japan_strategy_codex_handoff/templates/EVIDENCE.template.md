# Verification record

For each executed check, record the following values after the check actually runs. An empty record is not evidence.

- Test/scenario name and requirement IDs.
- Date, source revision, content version, and scenario seed.
- OS, engine, compiler, CPU/GPU/RAM, resolution/settings where relevant.
- Exact executable and command line, working directory, exit status.
- Pass/fail/block status and report/log path.
- Expected observable result and actual result.
- Screenshots/video for visible features, with description of what they prove.
- Measured frame-time distribution and memory for performance checks.
- Known limitations, untested platforms, and the exact next corrective step.

Never use example numbers as measurements. Never mark an unavailable tool's test as passing. Do not save secrets or unrelated user information in logs.
