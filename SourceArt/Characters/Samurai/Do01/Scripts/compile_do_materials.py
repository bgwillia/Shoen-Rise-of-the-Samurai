"""Compile review shader permutations on the real render device, without FBX import.

Run with UnrealEditor -ExecutePythonScript=<this file>, without -NullRHI/-game.
Native Manny material packages are read-only; only M_Do01 may be saved.
UE's GetStatistics submits missing shader jobs and waits for their completion.
"""
import hashlib
import json
from pathlib import Path
import traceback
import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve().parent
DO = "/Game/Art/Characters/Samurai/Do01"
NATIVE = "/Game/Characters/Mannequins/Materials"
OUT = ROOT / "artifacts/do01/material-compilation.json"
edit = u.MaterialEditingLibrary
report = {"validated": False, "rendering_validated": False, "materials": [],
          "scope": "Real-RHI shader compilation; no mesh, texture, animation or native material package edits"}


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def checkpoint(stage):
    report["stage"] = stage
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n")


def package_hash(path):
    file = Path(u.Paths.project_content_dir()) / (path.removeprefix("/Game/") + ".uasset")
    return hashlib.sha256(file.read_bytes()).hexdigest()


try:
    command = u.SystemLibrary.get_command_line()
    require("-nullrhi" not in command.lower() and "-game" not in command.lower().split(),
            "This material compilation pass requires Unreal Editor with a real renderer")
    report["command_line"] = command
    native_paths = [NATIVE + "/M_Mannequin", NATIVE + "/Manny/MI_Manny_01_New", NATIVE + "/Manny/MI_Manny_02_New"]
    before = {path: package_hash(path) for path in native_paths}
    materials = [u.load_asset(DO + "/M_Do01")] + [u.load_asset(path) for path in native_paths]
    require(all(materials), "Missing review material")
    armor = u.load_asset(DO + "/SK_Do01")
    require(armor is not None and armor.get_editor_property("materials")[0].material_interface == materials[0],
            "Skeletal Dō slot 0 is not assigned to M_Do01")
    mat = materials[0]
    report["do_usage"] = {name: bool(mat.get_editor_property(name)) for name in
                          ("used_with_skeletal_mesh", "used_with_instanced_static_meshes")}
    require(all(report["do_usage"].values()), "Dō material lacks required skeletal/instance usage flags")
    for material in materials:
        path = material.get_path_name()
        checkpoint("compiling missing permutations for " + path)
        entry = {"asset": path, "shader_types_before": edit.get_num_shader_types(material)}
        # This is the supported synchronous barrier in UE 5.8; unlike merely
        # queuing a recompile, it waits for the active device's shader resource.
        stats = edit.get_statistics(material)
        entry["statistics"] = {name: stats.get_editor_property(name) for name in
            ("num_vertex_shader_instructions", "num_pixel_shader_instructions", "num_samplers",
             "num_vertex_texture_samples", "num_pixel_texture_samples", "num_uv_scalars")}
        shaders = edit.list_shaders(material)
        entry["shader_types_after"] = edit.get_num_shader_types(material)
        entry["vertex_factories"] = sorted({str(shader.vertex_factory_name) for shader in shaders})
        entry["compiled_shaders"] = len(shaders)
        report["materials"].append(entry)
        checkpoint("compiled " + path)
        require(entry["compiled_shaders"] > 0 and entry["shader_types_after"] > 0,
                "No compiled active-device shader map: " + path)
    require(report["materials"][0]["statistics"]["num_samplers"] >= 3,
            "Dō shader did not retain its three texture samplers")
    require(u.EditorAssetLibrary.save_loaded_asset(mat, only_if_is_dirty=False), "Could not save Dō material")
    report["native_package_hashes"] = {path: {"before": before[path], "after": package_hash(path)} for path in native_paths}
    require(all(v["before"] == v["after"] for v in report["native_package_hashes"].values()),
            "Native material package changed")
    report["saved_assets"] = [mat.get_path_name()]
    report["validated"] = True
    checkpoint("complete; rendered verification still required")
except Exception:
    report["error"] = traceback.format_exc()
    checkpoint("failed")
    raise
