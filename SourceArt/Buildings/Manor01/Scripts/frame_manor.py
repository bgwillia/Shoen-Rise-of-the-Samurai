"""Frame the final authored manor for its source-art review image."""
from pathlib import Path
import bpy
ART=Path(__file__).resolve().parents[1];ROOT=ART.parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ART/'Manor01.blend'))
s=bpy.context.scene;s.render.resolution_x=1900;s.render.resolution_y=1050;s.camera.data.lens=61
try:s.view_settings.look='AgX - Medium High Contrast'
except TypeError:pass
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'Manor01.blend'))
s.render.filepath=str(ROOT/'artifacts/manor01/manor-three-quarter.png');bpy.ops.render.render(write_still=True)
