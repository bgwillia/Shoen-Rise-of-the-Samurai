"""Run inside Blender; verify saved edits export without touching production art."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

import bpy

ART = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ART / "Scripts"))
import export_kabuto as exporter


def runtime_hash():
    vertices = bpy.data.objects["SM_Kabuto01_LOD0"].data.vertices
    return hashlib.sha256(str([tuple(v.co) for v in vertices]).encode()).hexdigest()


with tempfile.TemporaryDirectory(prefix="kabuto-export-edit-") as directory:
    scratch = Path(directory)
    for name in ("Kabuto01.blend", "asset-manifest.json"):
        shutil.copy2(ART / name, scratch / name)
    bpy.ops.wm.open_mainfile(filepath=str(scratch / "Kabuto01.blend"))
    previous_runtime = runtime_hash()
    vertex = bpy.data.objects["Maedate"].data.vertices[0]
    vertex.co.x += .002
    expected = vertex.co.x
    bpy.ops.wm.save_as_mainfile(filepath=str(scratch / "Kabuto01.blend"))
    exporter.ART = scratch
    exporter.ROOT = scratch
    exporter.main()
    assert abs(bpy.data.objects["Maedate"].data.vertices[0].co.x - expected) < 1e-8
    assert previous_runtime != runtime_hash()
    report = {
        "source_edit_survived": True,
        "runtime_changed": True,
        "edited_component": "Maedate",
        "vertex_index": 0,
        "delta_metres": .002,
        "scope": "Temporary source copy; production model unchanged",
    }
    output = ART.parents[3] / "artifacts/kabuto01/export-preservation.json"
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
