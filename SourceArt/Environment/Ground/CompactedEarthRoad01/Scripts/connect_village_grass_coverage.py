import unreal as u,json
from pathlib import Path
m=u.load_asset('/Game/Art/Environment/Ground/CompactedEarthRoad01/M_VillageRoad40_ConnectedGrass')
nodes={n.get_name():n for n in u.MaterialEditingLibrary.get_material_expressions(m)}
original=json.loads(Path('/private/tmp/patch-material.json').read_text())
for key in ['MaterialExpressionCustom_24','MaterialExpressionCustom_25']:
 code=original[key]
 old='float band=1-smoothstep(edgeWidth-120,edgeWidth,abs(Road.y));'
 new=old+'''
// Connect the pale original-terrain pocket to the approved grass coverage.
float2 groundPatch=(W.xy-float2(-23440,-10350))/float2(650,950);
float patchDistance=length(groundPatch)+.045*sin(W.x*.007+W.y*.003);
float connectedGround=1-smoothstep(.55,1.25,patchDistance);
band=max(band,connectedGround);
'''
 assert old in code
 nodes[key].set_editor_property('code',code.replace(old,new))
u.MaterialEditingLibrary.recompile_material(m);u.EditorAssetLibrary.save_loaded_asset(m)
Path('/private/tmp/patch-coverage-saved.txt').write_text('Saved both matching local coverage masks')
