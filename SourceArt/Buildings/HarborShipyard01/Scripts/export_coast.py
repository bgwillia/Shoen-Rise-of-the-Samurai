"""Export the authored static coastal dressing from the harbor review scene."""
from pathlib import Path
import sys,bpy
ART=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ART.parent/'LumberCharcoal01/Scripts'))
from finish_asset import export_linear
bpy.ops.wm.open_mainfile(filepath=str(ART/'HarborShipyard01.blend'))
for name,objects in [('HS01_CoastalWater',[bpy.data.objects['Static rippled coastal surface']]),('HS01_CoastalVerge',[o for o in bpy.data.objects if o.name.startswith('Sparse coastal grass')])]:
 for o in objects:o.modifiers.new('Export triangles','TRIANGULATE')
 export_linear(ART/'Exports'/(name+'.fbx'),objects)
