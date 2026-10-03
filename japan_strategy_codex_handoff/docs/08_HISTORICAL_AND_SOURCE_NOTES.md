# Historical guardrails and verified reference entry points

Checked September 14, 2026. These references ground selected facts and technical capabilities, not every proposed mechanic. All balance values, forecasts, social coefficients, timelines, and sample names in the design are authored game choices.

## Correct the accumulated design shorthand

An 1180 starting point should not silently borrow the buildings, social institutions, or military roster of sixteenth-century Japan. The Met documents period distinctions in armor, including yoroi associated with high-ranking cavalry and twelfth-century dō-maru for infantry [S08]. Use that collection as an entry point, not as permission to copy every later armor shown on the same page. Specialist production and fine craftsmanship are credible themes; the exact apprenticeship and output model remains fictional.

Warrior rule and the imperial throne were distinct. The Met's Kamakura overview describes the emperor remaining at Kyoto while military government operated from Kamakura [S09]. The user's goal of becoming emperor is therefore labeled a deliberate alternate-history endpoint, not the normal promotion ladder of a provincial warrior. Do not remove that endpoint to "correct" the game.

The same overview describes changing religious currents and patronage [S09]. It does not justify a universal rule that religious populations submit peacefully. Model institutions, treatment, aid, and political support. Avoid presenting a timeless fixed bushido code, stereotyped ninja guilds, ubiquitous formal duels, universal meat husbandry, or modern-style social categories as established facts for 1180. Those specific topics require additional specialist sourcing before adding historical claims or named events.

Earlier European-style matchlocks, imagined advanced specimens, or extraordinary foreign access belong to explicitly marked alternate-technology scenarios unless the exact artifact and route are independently supported. The elite-only firearm requirement is a balance rule, not a claim about all historical firearm users. The package deliberately contains no real-world construction recipes.

MLIT describes an early national road framework known as the Seven Roads [S10]. That supports using constrained transport corridors as inspiration, but does not verify the handoff's authored beta routes, faction boundaries, place names, or 1180 road positions.

## Geography and asset rights

Natural Earth is a public-domain modern cartographic dataset suitable as an initial overview/coastline source [S07]. Its "10m" layer means **1:10 million map scale, not 10-meter terrain resolution**. It is generalized, not suitable for exact battle topography, and does not reconstruct medieval shorelines, settlements, or provinces. The coastline entry describes its coverage and limitations [S11]. Do not import modern borders/roads as medieval truth.

Use researched historical overlays and documented authored terrain for the tactical layer. If later using GSI, DEM, OSM, commercial, or museum imagery, check that exact dataset/asset's reuse terms and attribution; do not assume this package licenses them. A public reference image is not automatically a distributable game asset. Keep a source/provenance manifest.

## Technical references

S01. OpenAI, **Custom instructions with AGENTS.md**. Repository guidance is discovered by Codex; keep root instructions concise and point to subsystem documents. Verified entry URL redirects to official ChatGPT Learn documentation.
https://developers.openai.com/codex/guides/agents-md

S02. Epic Games, **Instanced Static Mesh Component in Unreal Engine**. Instancing is a tool for managing repeated meshes and Actor overhead, not a guarantee for animated crowds.
https://dev.epicgames.com/documentation/unreal-engine/instanced-static-mesh-component-in-unreal-engine?lang=en-US

S03. Epic Games, **Overview of Mass Entity in Unreal Engine**. Data-oriented entity framework and fragment model.
https://dev.epicgames.com/documentation/unreal-engine/overview-of-mass-entity-in-unreal-engine?lang=en-US

S04. Epic Games, **Overview of Mass Gameplay in Unreal Engine**. Representation, spawning, LOD, and related functionality. Verify APIs against the installed engine version.
https://dev.epicgames.com/documentation/unreal-engine/overview-of-mass-gameplay-in-unreal-engine?lang=en-US

S05. Epic Games, **Automation Test Framework** and **Run Automation Tests**. Actual project commands must be verified locally; these are capability/documentation references.
https://dev.epicgames.com/documentation/en-us/unreal-engine/automation-test-framework-in-unreal-engine
https://dev.epicgames.com/documentation/en-us/unreal-engine/run-automation-tests-in-unreal-engine

S06. Epic Games, **Saving and Loading Your Game**. Documents asynchronous save support; a consistent captured simulation snapshot still remains this project's responsibility.
https://dev.epicgames.com/documentation/en-us/unreal-engine/saving-and-loading-your-game-in-unreal-engine

## Map and history references

S07. Natural Earth, **Terms of Use**. Public-domain dataset policy; preserve provenance even when attribution is not required.
https://www.naturalearthdata.com/about/terms-of-use/

S08. The Metropolitan Museum of Art, **Art of the Samurai: Japanese Arms and Armor, 1156–1868**, collection/photo gallery. Period-labeled material and craft references.
https://www.metmuseum.org/exhibitions/listings/2009/art-of-the-samurai/photo-gallery

S09. The Metropolitan Museum of Art, **Kamakura and Nanbokucho Periods (1185–1392)**. Introductory political, artistic, and religious context, not a complete social-history source.
https://www.metmuseum.org/essays/kamakura-and-nanbokucho-periods-1185-1392

S10. Japan Ministry of Land, Infrastructure, Transport and Tourism, **History of Roads**. Broad historical transport framework, not a ready-made period GIS map.
https://www.mlit.go.jp/road/road_e/q1_history.html

S11. Natural Earth, **Coastline**. Scale, coverage, provenance, and generalization caveats.
https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-coastline/

## Research status fields for future content

Every historical entry should include `claim`, `date_range`, `region`, `source`, `source_type`, `confidence`, and `gameplay_deviation`. Use `historical_baseline`, `plausible_reconstruction`, or `alternate_history` as explicit labels. Named characters and exact duel narratives require dedicated verification; generic beta characters may be fictional and openly labeled.
