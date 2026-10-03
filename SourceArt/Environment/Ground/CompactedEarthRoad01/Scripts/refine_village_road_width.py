import unreal as u,json
from pathlib import Path
m=u.load_asset('/Game/Art/Environment/Ground/CompactedEarthRoad01/M_VillageRoad40_ConnectedGrass')
nodes={n.get_name():n for n in u.MaterialEditingLibrary.get_material_expressions(m)}
original=json.loads(Path('/private/tmp/road-width-original.json').read_text())
# Broad, nonrepeating changes: at most a few centimetres per edge over several metres.
def profile(q,p):
 return f'''float refineSection=smoothstep(1525,1850,{q}.x)*(1-smoothstep(4700,5100,{q}.x))*step({p}.y,-6500);
float widthChange=-.075*exp(-pow(({q}.x-2250)/400,2))+.035*exp(-pow(({q}.x-3350)/530,2))-.085*exp(-pow(({q}.x-4300)/440,2));
float refinedWidth=1+refineSection*widthChange;
'''
c=original['MaterialExpressionCustom_14']
c=profile('Q','P')+c.replace('smoothstep(92,125,abs(Q.y))','smoothstep(92*refinedWidth,125*refinedWidth,abs(Q.y))')
nodes['MaterialExpressionCustom_14'].set_editor_property('code',c)
c=profile('Q','P')+original['MaterialExpressionCustom_15']
c=c.replace('float u=saturate','widen*=refinedWidth;\nfloat u=saturate')
c=c.replace('float replace=section*edge*(.90-.53*remain);','''float replace=section*edge*(.90-.53*remain);
float pocketCentre=Q.y<0?2350:3920;
float quietShoulder=exp(-pow((Q.x-pocketCentre)/340,2))*refineSection;
replace=lerp(replace,max(replace,.94*smoothstep(35,65,abs(Q.y))),quietShoulder*.85);''')
nodes['MaterialExpressionCustom_15'].set_editor_property('code',c)
c=profile('Road','W')+original['MaterialExpressionCustom_24']
c=c.replace('smoothstep(135,205,abs(Road.y))','smoothstep(135*refinedWidth,205*refinedWidth,abs(Road.y))')
nodes['MaterialExpressionCustom_24'].set_editor_property('code',c)
u.MaterialEditingLibrary.recompile_material(m)
u.EditorAssetLibrary.save_loaded_asset(m)
Path('/private/tmp/road-width-applied.txt').write_text('Applied and saved existing material: '+m.get_path_name())
