"""Run inside Unreal Editor via tools/dev.py create-map; writes real engine packages."""
import unreal
from pathlib import Path

MAP = "/Game/Domain/Maps/Foundation"
map_file = Path(unreal.Paths.project_content_dir()) / "Domain/Maps/Foundation.umap"
# UE 5.8's NullRHI startup does not instantiate LevelEditorSubsystem.
# These verified UnrealEd utilities operate on real UWorld packages directly.
if map_file.exists():
    if not unreal.EditorLoadingAndSavingUtils.load_map(str(map_file.resolve())):
        raise RuntimeError("Existing Foundation map could not be loaded")
else:
    world = unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    if not world:
        raise RuntimeError("Unreal could not create Foundation map")
    if not unreal.EditorLoadingAndSavingUtils.save_map(world, MAP):
        raise RuntimeError("Unreal could not save Foundation map")
unreal.log("SHOEN_MAP_VERIFIED " + MAP)
