# Example data contracts

These files are valid illustrative JSON, not a claim that a game loader already exists. Codex must implement validation/import and map them to the shared C++ types. Do not copy scenario values into production code as hardcoded constants.

`beta_balance.json` captures the proposed headline defaults. `route_graph.json` is a connected topology fixture with schematic positions only: it is NOT historical GIS data and must not be rendered and described as a verified real map. `origin_ledger_fixture.json` provides all 100 exact service records for the casualty regression example. Its JSON Schema is included. `encounter_trace.json` demonstrates reachable sites and an event-backed narrative contract. `artifact_contracts.json` distinguishes an authored normal artifact chain from a separately labeled alternate-technology gunpowder laboratory.

The origin fixture is closed: 420 initial people, 200 eligible workers, 100 deployed, 10 dead, 15 wounded, 5 captive, and 70 healthy survivors. Of the 420 people, 410 remain alive after the battle. The 100 workers not mobilized are still available; returning 70 healthy survivors makes 170 available; recovering another five makes 175. Do not return wounded or captive people to full work before their actual status changes.

Every future runtime definition needs unique IDs, explicit units, valid references, and a content-version strategy. The map, artifact, and balance files demonstrate concepts; the Codex implementation must finish the full beta content described in the specification rather than assume these are all required content.
