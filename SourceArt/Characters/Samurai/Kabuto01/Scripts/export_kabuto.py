"""Export the saved, authoritative Kabuto01.blend without rebuilding its source.

Only the EXPORT ONLY collection, external textures/FBXs and manifest are
regenerated. Editable component geometry, modifiers, materials and fit fixtures
remain in the source file. Run validation after export, then Unreal import.
"""
import hashlib
import json
from pathlib import Path
import struct
import sys

import bpy

ART = Path(__file__).resolve().parents[1]
ROOT = ART.parents[3]
sys.path.insert(0, str(ART / 'Scripts'))
from kabuto_export_common import (COMPONENT_ORDER, RUNTIME_COLLECTION, SOURCE_COLLECTION,
                                  export_runtime, triangles)


def geometry_signature(objects):
    """Check that export operations did not alter the editable mesh data/poses."""
    digest = hashlib.sha256()
    for ob in objects:
        digest.update(ob.name.encode())
        for row in ob.matrix_world:
            digest.update(struct.pack('<4f', *row))
        for vertex in ob.data.vertices:
            digest.update(struct.pack('<3f', *vertex.co))
        for polygon in ob.data.polygons:
            digest.update(struct.pack('<II', len(polygon.vertices), polygon.material_index))
            digest.update(struct.pack('<' + 'I' * len(polygon.vertices), *polygon.vertices))
        for layer in ob.data.uv_layers:
            digest.update(layer.name.encode())
            for loop in layer.data:
                digest.update(struct.pack('<2f', *loop.uv))
        for material in ob.data.materials:
            digest.update(material.name.encode())
        digest.update(json.dumps([(mod.name, mod.type) for mod in ob.modifiers]).encode())
    return digest.hexdigest()


def main():
    source = ART / 'Kabuto01.blend'
    original_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene = bpy.context.scene
    if scene.unit_settings.system != 'METRIC' or abs(scene.unit_settings.scale_length - 1) > 1e-6:
        raise RuntimeError('Kabuto01 export expects the saved metre-unit source')
    components = [ob for ob in bpy.data.collections[SOURCE_COLLECTION].objects if ob.type == 'MESH']
    # Keep reduction input order equal to construction, regardless of collection
    # iteration order after reopening Blender. Added components follow by name.
    order = {name: index for index, name in enumerate(COMPONENT_ORDER)}
    components.sort(key=lambda ob: (order.get(ob.name, len(order)), ob.name))
    body, rig = bpy.data.objects['FIT_MaleBody'], bpy.data.objects['FIT_Rig']
    pivot = rig.matrix_world @ rig.data.bones['head'].head_local
    runtime = bpy.data.collections.get(RUNTIME_COLLECTION)
    if runtime is None:
        runtime = bpy.data.collections.new(RUNTIME_COLLECTION)
        scene.collection.children.link(runtime)
    before = geometry_signature([*components, body])
    lods, evaluated_count = export_runtime(components, runtime, ART, pivot, body, rig)
    bpy.context.view_layer.update()
    after = geometry_signature([*components, body])
    if before != after:
        raise RuntimeError('Export changed editable mesh data/transforms; source file was not saved')

    texture_files = []
    for suffix in ('BaseColor', 'Normal', 'ORM'):
        image = bpy.data.images['T_Kabuto01_' + suffix]
        path = ART / 'Textures' / (image.name + '.png')
        path.parent.mkdir(parents=True, exist_ok=True)
        image.filepath_raw = str(path)
        image.file_format = 'PNG'
        image.save()
        image.pack()
        texture_files.append(path)
    # Save the artist source with fresh hidden runtime copies, not regenerated
    # construction. Blender's normal .blend1 backup behavior is retained.
    bpy.ops.wm.save_as_mainfile(filepath=str(source))
    manifest_file = ART / 'asset-manifest.json'
    manifest = json.loads(manifest_file.read_text()) if manifest_file.exists() else {'asset': 'Kabuto01'}
    manifest.update({
        'blender_version': bpy.app.version_string,
        'source_components': {ob.name: triangles(ob) for ob in components},
        'source_component_objects': len(components),
        'source_triangles_before_modifiers': sum(triangles(ob) for ob in components),
        'evaluated_source_triangles': evaluated_count,
        'exported_triangles': triangles(lods[0]),
        'runtime_lod_triangles': [triangles(ob) for ob in lods],
        'runtime_materials': len(lods[0].data.materials),
        'source_materials': len({mat.name for ob in components for mat in ob.data.materials}),
        'head_pivot_metres': list(pivot),
        'helmet_bounds_head_relative_metres': [
            [min(vertex.co[axis] for vertex in lods[0].data.vertices) for axis in range(3)],
            [max(vertex.co[axis] for vertex in lods[0].data.vertices) for axis in range(3)]],
        'export_operation': 'Saved Blender source -> evaluated runtime copies; no source reconstruction',
        'exported_from_source_sha256': original_hash,
        'source_blend_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'editable_geometry_sha256': after,
        'editable_geometry_preserved_during_export': True,
        'reduction_ratios': [float(ob.get("runtime_reduction_ratio", 1.0)) for ob in lods],
    })
    files = [*sorted((ART / 'Exports').glob('*.fbx')),
             *sorted((ART / 'Review/Exports').glob('*.fbx')), *texture_files]
    manifest['export_files'] = {
        str(path.relative_to(ART)): {'bytes': path.stat().st_size,
                                    'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        for path in files}
    manifest_file.write_text(json.dumps(manifest, indent=2, allow_nan=False) + '\n')
    print('KABUTO01_SAVED_SOURCE_EXPORTED ' + json.dumps({
        'source': str(source.relative_to(ROOT)),
        'runtime_lod_triangles': manifest['runtime_lod_triangles'],
        'editable_geometry_preserved_during_export': True}))


if __name__ == '__main__':
    main()
