import unreal as u,json
from pathlib import Path
path='/Game/Cinematics/LandBridgeComedy/A_Manny_BridgeComedy'
a=u.load_asset(path) or u.EditorAssetLibrary.duplicate_asset('/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle',path)
c=a.get_editor_property('controller');c.open_bracket('Land bridge cinematic motion',False);c.set_frame_rate(u.FrameRate(30,1),False);c.set_number_of_frames(u.FrameNumber(360),False)
tracks=json.loads(Path('/private/tmp/cine-tracks.json').read_text())
for n,(pp,qq) in tracks.items():
 c.add_bone_track(n,False)
 c.set_bone_track_keys(n,[u.Vector(*p) for p in pp],[u.Quat(*q) for q in qq],[u.Vector(1,1,1)]*len(pp),False)
c.close_bracket(False);u.EditorAssetLibrary.save_loaded_asset(a)
Path('/private/tmp/cine-anim-ready.txt').write_text(a.get_path_name())
