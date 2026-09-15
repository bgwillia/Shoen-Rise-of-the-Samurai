# Kusazuri01 visual review

## Reference and requested correction

The supplied reference prioritizes a flared, separated lamellar skirt; black lacquer, red lacing, restrained brass, an indigo obi and finished inner padding. The user confirmed the design but rejected the first finish as amateurish relative to the helmet and Dō.

The revision preserves the seven-leaf outline. It replaces plain plate faces with the same full lamella atlas used by Dō, adds sparse raised fastenings aligned with that atlas, refines the edge treatment and substitutes physically braided indigo cords with wrapped knots for the simpler obi. These are actual mesh, UV and material changes.

## Inspected during revision

- `SourceArt/Characters/Samurai/Kusazuri01/Review/Captures/component-refined.png`: the curved individual lamellae, paired red fastening tiers, narrow dark row bindings, brass accents and indigo knot read as a coherent armor component. The regular repeated pattern is simpler than the concept sheet.
- `artifacts/kusazuri01/waist-final-r035.png`: the new finish matches the Dō closely. The raised obi sits against the lower hem with shallow attachment contact. Narrow white body slivers below the belt prompted an upward extension of the panel lining.
- `artifacts/kusazuri01/lod2-r035-front.png`: **rejected**. Global collapse removed the lacquered plate faces and left lining. Retained bone groups and bounds alone were insufficient evidence of coverage. Export was revised to protect shells and the lower hem; validation now checks lacquer-atlas faces on every leaf.

## Mesh checks before the final tail/material adjustment

- [Final fitted waist](waist-final-final.png): the lining closes the former white slivers. The obi sits against the Dō hem, and the finish uses the same lamella texture and fastening scale as the torso. The lower lacquer is slightly darker, consistent with its Sode-derived material variant.
- [Final LOD2 front](lod2-final-front.png): all visible panel shells and horizontal lacquer/red-lace courses remain. The closed lower hem remains, while its geometric diamond ornament and most tiny raised cords are intentionally absent at distance. The knot is coarse when magnified; this is a distant mesh, not the close-view asset.

Final source and Unreal views are listed in [verification.md](verification.md). Historical images above explain revisions and are not final acceptance evidence. No human visual approval is claimed.

## Final frozen source and actual Unreal checks

Final source SHA:`cf7c0ec0578b7fe2aca7d1b30439c521e8cecc3e63d4f36b0c8820b31dc9eb9e`.

- [Saved-source underside](underside-final-cloth.png): the padded backing is dark indigo with subdued quilt relief. The former pale grazing highlight is gone; metal highlights remain along the edges.
- [Actual Metal waist detail](final-detail.png): lacquer and red lacing match the torso's construction language; brass bindings are narrow, and the braided obi sits beneath the Dō hem. The regular atlas repeats are still visible at this close range.
- [Actual Metal low-angle outfit](final-interior.png): the camera now remains above the floor and shows the lower hems, knot and dark interior edges. Manny's thighs obscure most padding, so this is not the primary isolated interior proof.
- [Actual Metal overhead outfit](final-top.png): the assembled existing helmet/torso/shoulders and new waist are visible. Upper equipment occludes the waist interior, which is shown separately in the source component views.

Native review uses the unchanged white Manny body. Gaps between independently hanging leaves expose that fixture; no trousers or underclothing have been created in this component-only task.

- Fresh [component three-quarter front](../../SourceArt/Characters/Samurai/Kusazuri01/Review/Captures/threequarter-front.png): all seven courses remain legible, plate faces curve across each leaf, and the shortened tassels retain the reference's centered belt knot. The finish is intentionally regular compared with the illustration.
- Fresh [exploded construction](../../SourceArt/Characters/Samurai/Kusazuri01/Review/Captures/exploded-construction.png): shells, backing, lacing and edge hardware remain separately editable; the image uses temporary presentation offsets and does not alter the saved source.

- [Actual500-figure tactical check](cost-500-kusazuri.png) and [100-figure check](cost-100-kusazuri.png): full formations render at the shared distant camera without missing outfits or displaced waist assemblies. Figures are small at this distance, so these frames establish group rendering/readability only; the separate component and close captures establish surface quality.
