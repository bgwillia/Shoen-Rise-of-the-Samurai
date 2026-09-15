"""Read-only reproduction of saved LOD2 corner-normal failures."""
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sode_common import ART, ROOT, common

bpy.ops.wm.open_mainfile(filepath=str(ART / 'Sode01.blend'))
rig = bpy.data.objects['root']
rig.data.pose_position = 'REST'
if rig.animation_data:
    rig.animation_data.action = None
    rig.animation_data.use_nla = False
rig.matrix_basis = Matrix.Diagonal((.01, .01, .01, 1.))
rig.hide_set(False)
bpy.context.view_layer.update()


def inspect(mesh):
    lookup = {loop: polygon for polygon in mesh.polygons for loop in polygon.loop_indices}
    records = []
    for index, normal in enumerate(mesh.corner_normals):
        vector = normal.vector
        if all(math.isfinite(value) for value in vector) and abs(vector.length-1) <= .001:
            continue
        polygon = lookup[index]
        points = [mesh.vertices[i].co.copy() for i in polygon.vertices]
        geometric = (points[1]-points[0]).cross(points[2]-points[0])
        records.append({'loop': index, 'vertex': mesh.loops[index].vertex_index,
            'polygon': polygon.index, 'smooth': polygon.use_smooth,
            'normal': list(vector), 'length': vector.length, 'triangle_cross_length': geometric.length,
            'geometric_normal': list(geometric.normalized()), 'points': [list(point) for point in points]})
    return records


report = {}
for name in ('SK_Sode_L_01_LOD2', 'SM_Sode_L_01_LOD2', 'SK_Sode_R_01_LOD2'):
    ob = bpy.data.objects[name]
    ob.hide_set(False)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    evaluated = ob.evaluated_get(dg)
    mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=dg)
    report[name] = {'raw': inspect(ob.data), 'evaluated': inspect(mesh),
        'reported_fallbacks': ob.get('geometric_normal_fallback_corners')}
    evaluated.to_mesh_clear()
    copy = ob.copy()
    copy.data = ob.data.copy()
    bpy.context.scene.collection.objects.link(copy)
    copy.modifiers.clear()
    common.surface_normals(copy)
    report[name]['temporary_copy_after_normal_helper'] = inspect(copy.data)
    report[name]['new_fallback_count'] = copy.get('geometric_normal_fallback_corners')
    # Replay local scale change separately to identify where validity changes.
    copy.data.transform(Matrix.Scale(.01, 4))
    common.surface_normals(copy)
    report[name]['temporary_metres_after_normal_helper'] = inspect(copy.data)
    copy.data.transform(Matrix.Scale(100., 4))
    report[name]['after_transform_back_to_cm'] = inspect(copy.data)
    bpy.data.objects.remove(copy, do_unlink=True)

output = ROOT / 'artifacts/sode01/normal-diagnostic.json'
output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
print('SODE_NORMAL_DIAGNOSTIC ' + json.dumps(report), flush=True)
