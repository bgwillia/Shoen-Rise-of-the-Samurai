"""Render deformation proof from saved source, without modifying the .blend."""
import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Samurai01.blend'))
scene=bpy.context.scene; scene.cycles.samples=32
scene.render.resolution_x=880; scene.render.resolution_y=1040
rig=bpy.data.objects['RIG_Samurai01']
for name,action,frame in [('walk','A_Walk',9),('attack','A_Attack',24)]:
    rig.animation_data.action=bpy.data.actions[action]; scene.frame_set(frame)
    scene.render.filepath=str(ROOT/f'preview-{name}.png')
    bpy.ops.render.render(write_still=True)
print('SHOEN_POSE_RENDERS_WRITTEN')
