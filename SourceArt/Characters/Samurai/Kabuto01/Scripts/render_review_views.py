"""Render actual saved source rear, top and interior views without editing it."""
from pathlib import Path
import bpy
from mathutils import Vector

ART=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ART/'Kabuto01.blend'))
scene=bpy.context.scene
scene.cycles.samples=20
scene.render.resolution_x=900
scene.render.resolution_y=900
scene.render.resolution_percentage=100
camera=scene.camera
camera.data.ortho_scale=.53
for name,position,target in [
    ('rear',(0,1.2,1.90),(0,.02,1.70)),
    ('top',(0,.015,3),(0,.015,1.70)),
    ('interior',(0,-.16,.7),(0,.025,1.72)),
]:
    if name=='interior':
        light=bpy.data.lights.new('Interior inspection fill','AREA')
        light.energy=8; light.size=.35
        lamp=bpy.data.objects.new('Interior inspection fill',light)
        scene.collection.objects.link(lamp); lamp.location=(0,-.06,1.2)
        lamp.rotation_euler=(Vector((0,.015,1.72))-lamp.location).to_track_quat('-Z','Y').to_euler()
    camera.location=position
    camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(ART/f'Review/Captures/blender-{name}.png')
    bpy.ops.render.render(write_still=True)
