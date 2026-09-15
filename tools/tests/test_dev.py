import json
import importlib.util
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest


REPOSITORY = Path(__file__).resolve().parents[2]
DEV = REPOSITORY / "tools" / "dev.py"


def load_dev_module():
    spec = importlib.util.spec_from_file_location("shoen_dev", DEV)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_executable(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(source).lstrip(), encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


class DevCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "game").mkdir()
        (self.root / "game" / "Shoen.uproject").write_text("{}\n", encoding="utf-8")
        (self.root / "core").mkdir()
        (self.root / "core" / "CMakeLists.txt").write_text(
            "cmake_minimum_required(VERSION 3.25)\n", encoding="utf-8"
        )
        (self.root / "tools").mkdir()
        (self.root / "tools" / "create_foundation.py").write_text(
            "# executed by the fake editor\n", encoding="utf-8"
        )
        self.bin = self.root / "fake-bin"
        self.bin.mkdir()
        self.calls = self.root / "calls.jsonl"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def env(self, **extra: str) -> dict[str, str]:
        result = os.environ.copy()
        result["PATH"] = os.pathsep.join((str(self.bin), result.get("PATH", "")))
        result["SHOEN_REPO_ROOT"] = str(self.root)
        result["SHOEN_FAKE_CALLS"] = str(self.calls)
        result.update(extra)
        return result

    def run_cli(
        self,
        *arguments: str,
        env: dict[str, str] | None = None,
        timeout: float = 10,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(DEV), *arguments],
            cwd=self.root,
            env=env or self.env(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )

    def read_calls(self) -> list[dict[str, object]]:
        return [json.loads(line) for line in self.calls.read_text(encoding="utf-8").splitlines()]

    def install_recorder(self, path: Path, body: str = "") -> None:
        source = """#!/usr/bin/env python3
import json
import os
from pathlib import Path
import sys
import time

with Path(os.environ["SHOEN_FAKE_CALLS"]).open("a", encoding="utf-8") as stream:
    stream.write(json.dumps({"program": Path(sys.argv[0]).name, "argv": sys.argv[1:]}) + "\\n")
"""
        write_executable(path, source + textwrap.dedent(body).lstrip())

    def make_engine(self, editor_body: str = "") -> Path:
        engine = self.root / "UE_5.8"
        build_version = engine / "Engine" / "Build" / "Build.version"
        build_version.parent.mkdir(parents=True)
        build_version.write_text(
            json.dumps(
                {
                    "MajorVersion": 5,
                    "MinorVersion": 8,
                    "PatchVersion": 2,
                    "Changelist": 56702186,
                    "CompatibleChangelist": 56603056,
                    "BranchName": "++UE5+Release-5.8",
                }
            ),
            encoding="utf-8",
        )
        self.install_recorder(
            engine / "Engine" / "Binaries" / "Mac" / "UnrealEditor.app" / "Contents" / "MacOS" / "UnrealEditor",
            editor_body,
        )
        self.install_recorder(engine / "Engine" / "Build" / "BatchFiles" / "Mac" / "Build.sh")
        self.install_recorder(engine / "Engine" / "Build" / "BatchFiles" / "RunUAT.sh")
        return engine

    def install_core_tools(self, cmake_exit: int = 0, ctest_exit: int = 0) -> None:
        self.install_recorder(self.bin / "cmake", f"raise SystemExit({cmake_exit})")
        self.install_recorder(self.bin / "ctest", f"raise SystemExit({ctest_exit})")

    def test_engine_command_fails_when_engine_root_is_missing(self) -> None:
        result = self.run_cli("--engine", str(self.root / "missing-engine"), "build")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unreal Engine", result.stdout)
        self.assertIn("missing-engine", result.stdout)

    def test_engine_option_is_accepted_after_the_subcommand(self) -> None:
        engine = self.make_engine()

        result = self.run_cli("build", "--engine", str(engine))

        self.assertEqual(result.returncode, 0, result.stdout)

    def test_core_test_never_requires_or_invokes_unreal(self) -> None:
        self.install_core_tools()

        result = self.run_cli(
            "--engine",
            str(self.root / "missing-engine"),
            "core-test",
            "--suite",
            "ledger",
        )

        self.assertEqual(result.returncode, 0, result.stdout)
        calls = self.read_calls()
        self.assertEqual([call["program"] for call in calls], ["cmake", "cmake", "ctest"])
        self.assertEqual(calls[2]["argv"][-2:], ["-R", "ledger"])
        self.assertNotIn("Unreal", result.stdout)

    def test_child_failure_is_propagated_and_logged(self) -> None:
        self.install_core_tools(ctest_exit=17)

        result = self.run_cli("core-test")

        self.assertEqual(result.returncode, 17, result.stdout)
        log = self.root / "artifacts" / "tooling-core-test.log"
        self.assertTrue(log.is_file())
        self.assertIn("fake-bin/ctest", log.read_text(encoding="utf-8"))

    def test_core_suite_filter_fails_when_ctest_matches_no_tests(self) -> None:
        self.install_recorder(self.bin / "cmake")
        self.install_recorder(
            self.bin / "ctest",
            """
            if "-R" in sys.argv and "does-not-exist" in sys.argv and "--no-tests=error" in sys.argv:
                raise SystemExit(5)
            """,
        )

        result = self.run_cli("core-test", "--suite", "does-not-exist")

        self.assertNotEqual(result.returncode, 0, result.stdout)

    def test_build_uses_editor_target_and_prints_an_argument_array(self) -> None:
        engine = self.make_engine()

        result = self.run_cli("--engine", str(engine), "build")

        self.assertEqual(result.returncode, 0, result.stdout)
        call = self.read_calls()[0]
        self.assertEqual(call["program"], "Build.sh")
        self.assertEqual(call["argv"][:3], ["ShoenEditor", "Mac", "Development"])
        self.assertEqual(call["argv"][3], str((self.root / "game" / "Shoen.uproject").resolve()))
        self.assertIn("-WaitMutex", call["argv"])
        printed = json.loads(result.stdout.splitlines()[0].removeprefix("+ "))
        self.assertEqual(printed[1:4], ["ShoenEditor", "Mac", "Development"])

    def test_create_map_requires_the_real_umap_output(self) -> None:
        engine = self.make_engine()

        result = self.run_cli("--engine", str(engine), "create-map")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Foundation.umap", result.stdout)
        argv = self.read_calls()[0]["argv"]
        self.assertIn(
            f"-ExecutePythonScript={(self.root / 'tools' / 'create_foundation.py').resolve()}", argv
        )

    def test_create_map_accepts_only_an_editor_generated_umap(self) -> None:
        map_path = self.root / "game" / "Content" / "Domain" / "Maps" / "Foundation.umap"
        editor_body = f"""
        output = Path({str(map_path)!r})
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b'UE-map')
        """
        engine = self.make_engine(editor_body)

        result = self.run_cli("--engine", str(engine), "create-map")

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertTrue(map_path.is_file())

    def test_editor_test_rejects_missing_or_empty_reports(self) -> None:
        engine = self.make_engine()

        result = self.run_cli("--engine", str(engine), "editor-test", "--suite", "foundation")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("automation report", result.stdout.lower())
        argv = self.read_calls()[0]["argv"]
        self.assertIn("-ExecCmds=Automation RunTests Shoen.Foundation", argv)
        self.assertIn("-TestExit=Automation Test Queue Empty", argv)
        self.assertIn("-NullRHI", argv)

    def test_editor_test_parses_successful_matching_tests(self) -> None:
        editor_body = """
        report = next(value.split("=", 1)[1] for value in sys.argv if value.startswith("-ReportExportPath="))
        output = Path(report)
        output.mkdir(parents=True, exist_ok=True)
        (output / "index.json").write_text(json.dumps({
            "tests": [{"testDisplayName": "Shoen.Foundation.Ledger", "state": "Success", "errors": 0}]
        }), encoding="utf-8-sig")
        """
        engine = self.make_engine(editor_body)

        result = self.run_cli("--engine", str(engine), "editor-test", "--suite", "foundation")

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("1 automation test passed", result.stdout)

    def test_editor_test_rejects_failed_and_skipped_tests(self) -> None:
        editor_body = """
        report = next(value.split("=", 1)[1] for value in sys.argv if value.startswith("-ReportExportPath="))
        output = Path(report)
        output.mkdir(parents=True, exist_ok=True)
        (output / "index.json").write_text(json.dumps({
            "tests": [
                {"testDisplayName": "Shoen.Foundation.Save", "state": "Fail", "errors": 1},
                {"testDisplayName": "Shoen.Foundation.Camera", "state": "Skipped", "errors": 0}
            ]
        }), encoding="utf-8")
        """
        engine = self.make_engine(editor_body)

        result = self.run_cli("--engine", str(engine), "editor-test", "--suite", "foundation")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Fail", result.stdout)
        self.assertIn("Skipped", result.stdout)

    def test_editor_test_selects_and_validates_placement_suite(self) -> None:
        editor_body = """
        report = next(value.split("=", 1)[1] for value in sys.argv if value.startswith("-ReportExportPath="))
        output = Path(report)
        output.mkdir(parents=True, exist_ok=True)
        (output / "index.json").write_text(json.dumps({
            "tests": [{"fullTestPath": "Shoen.Placement.Storehouse", "state": "Success", "errors": 0}]
        }), encoding="utf-8-sig")
        """
        engine = self.make_engine(editor_body)

        result = self.run_cli("--engine", str(engine), "editor-test", "--suite", "placement")

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("1 automation test passed from Shoen.Placement", result.stdout)
        argv = self.read_calls()[0]["argv"]
        self.assertIn("-ExecCmds=Automation RunTests Shoen.Placement", argv)
        self.assertNotIn("-ExecCmds=Automation RunTests Shoen.Foundation", argv)

    def test_editor_test_rejects_missing_placement_report(self) -> None:
        engine = self.make_engine()

        result = self.run_cli("--engine", str(engine), "editor-test", "--suite", "placement")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("automation report", result.stdout.lower())

    def test_editor_test_rejects_failed_placement_report(self) -> None:
        editor_body = """
        report = next(value.split("=", 1)[1] for value in sys.argv if value.startswith("-ReportExportPath="))
        output = Path(report)
        output.mkdir(parents=True, exist_ok=True)
        (output / "index.json").write_text(json.dumps({
            "tests": [{"fullTestPath": "Shoen.Placement.Overlap", "state": "Fail", "errors": 1}]
        }), encoding="utf-8-sig")
        """
        engine = self.make_engine(editor_body)

        result = self.run_cli("--engine", str(engine), "editor-test", "--suite", "placement")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("shoen.placement.overlap: fail", result.stdout.lower())

    def test_run_passes_scenario_and_soldier_count_as_game_flags(self) -> None:
        engine = self.make_engine()

        result = self.run_cli(
            "--engine", str(engine), "run", "--scenario", "scale_lab", "--soldiers", "4000"
        )

        self.assertEqual(result.returncode, 0, result.stdout)
        argv = self.read_calls()[0]["argv"]
        self.assertIn("/Game/Domain/Maps/Foundation", argv)
        self.assertIn("-game", argv)
        self.assertIn("-windowed", argv)
        self.assertIn("-ResX=1600", argv)
        self.assertIn("-ResY=900", argv)
        self.assertIn("-NoVSync", argv)
        self.assertIn("-ShoenScenario=scale_lab", argv)
        self.assertIn("-ShoenSoldiers=4000", argv)

    def test_run_passes_settlement_scenario_on_the_foundation_map(self) -> None:
        engine = self.make_engine()

        result = self.run_cli("--engine", str(engine), "run", "--scenario", "settlement")

        self.assertEqual(result.returncode, 0, result.stdout)
        argv = self.read_calls()[0]["argv"]
        self.assertIn("/Game/Domain/Maps/Foundation", argv)
        self.assertIn("-ShoenScenario=settlement", argv)
        self.assertNotIn("-ShoenScenario=foundation", argv)
        self.assertNotIn("-ShoenScenario=scale_lab", argv)

    def test_benchmark_is_rendered_and_requires_valid_fresh_counts(self) -> None:
        editor_body = """
        output_arg = next(value for value in sys.argv if value.startswith("-ShoenBenchmarkOutput="))
        output = Path(output_arg.split("=", 1)[1])
        soldiers = int(next(value.split("=", 1)[1] for value in sys.argv if value.startswith("-ShoenSoldiers=")))
        seconds = float(next(value.split("=", 1)[1] for value in sys.argv if value.startswith("-ShoenBenchmarkSeconds=")))
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps({
            "mode": "rendered_primitive_movement_only",
            "requested_soldiers": soldiers,
            "live_soldiers": soldiers,
            "formations": soldiers // 100,
            "seconds": seconds,
            "frames": 7200,
            "median_frame_ms": 12.5,
            "p95_frame_ms": 18.75,
            "median_fps": 80.0,
            "peak_process_memory_bytes": 1073741824,
            "viewport_width": 1600,
            "viewport_height": 900,
            "simulation_cpu_median_ms": 0.25,
            "simulation_cpu_p95_ms": 0.5
        }), encoding="utf-8-sig")
        """
        engine = self.make_engine(editor_body)

        result = self.run_cli(
            "--engine", str(engine), "benchmark", "--soldiers", "8000", "--seconds", "120"
        )

        self.assertEqual(result.returncode, 0, result.stdout)
        argv = self.read_calls()[0]["argv"]
        self.assertIn("-game", argv)
        self.assertNotIn("-NullRHI", argv)
        self.assertIn("-windowed", argv)
        self.assertIn("-ResX=1600", argv)
        self.assertIn("-ResY=900", argv)
        self.assertIn("-NoVSync", argv)
        self.assertIn("-ShoenBenchmarkSeconds=120", argv)
        self.assertIn("-ShoenSoldiers=8000", argv)
        self.assertIn("-ShoenScenario=scale_lab", argv)

    def test_benchmark_rejects_a_report_with_wrong_counts(self) -> None:
        editor_body = """
        output_arg = next(value for value in sys.argv if value.startswith("-ShoenBenchmarkOutput="))
        output = Path(output_arg.split("=", 1)[1])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps({
            "requested_soldiers": 8000,
            "live_soldiers": 7999,
            "formations": 80,
            "seconds": 120
        }), encoding="utf-8")
        """
        engine = self.make_engine(editor_body)

        result = self.run_cli("--engine", str(engine), "benchmark", "--soldiers", "8000")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("live_soldiers", result.stdout)

    def test_benchmark_rejects_missing_invalid_or_nonfinite_measurements(self) -> None:
        dev = load_dev_module()
        valid = {
            "mode": "rendered_primitive_movement_only",
            "requested_soldiers": 8000,
            "live_soldiers": 8000,
            "formations": 80,
            "seconds": 120,
            "frames": 7200,
            "median_frame_ms": 12.5,
            "p95_frame_ms": 18.75,
            "median_fps": 80.0,
            "peak_process_memory_bytes": 1073741824,
            "viewport_width": 1600,
            "viewport_height": 900,
            "simulation_cpu_median_ms": 0.25,
            "simulation_cpu_p95_ms": 0.5,
        }
        mutations = (
            ("mode", "headless", "mode"),
            ("frames", 0, "frames"),
            ("frames", 1.5, "frames"),
            ("median_frame_ms", 0, "median_frame_ms"),
            ("median_frame_ms", float("nan"), "median_frame_ms"),
            ("p95_frame_ms", 10, "p95_frame_ms"),
            ("p95_frame_ms", float("inf"), "p95_frame_ms"),
            ("median_fps", 0, "median_fps"),
            ("median_fps", float("inf"), "median_fps"),
            ("peak_process_memory_bytes", 0, "peak_process_memory_bytes"),
            ("viewport_width", 0, "viewport_width"),
            ("viewport_height", -1, "viewport_height"),
            ("simulation_cpu_median_ms", -1, "simulation_cpu_median_ms"),
            ("simulation_cpu_median_ms", float("nan"), "simulation_cpu_median_ms"),
            ("simulation_cpu_p95_ms", 0.1, "simulation_cpu_p95_ms"),
            ("simulation_cpu_p95_ms", float("inf"), "simulation_cpu_p95_ms"),
        )
        for field, value, expected_problem in mutations:
            with self.subTest(field=field, value=value):
                report = dict(valid)
                report[field] = value
                path = self.root / f"invalid-{field}.json"
                path.write_text(json.dumps(report), encoding="utf-8")

                problems = dev.validate_benchmark_report(path, 8000, 120)

                self.assertTrue(
                    any(expected_problem in problem for problem in problems),
                    f"expected {expected_problem!r} problem, got {problems!r}",
                )

    def test_benchmark_requires_every_measurement_field(self) -> None:
        dev = load_dev_module()
        path = self.root / "counts-only.json"
        path.write_text(
            json.dumps(
                {
                    "requested_soldiers": 8000,
                    "live_soldiers": 8000,
                    "formations": 80,
                    "seconds": 120,
                }
            ),
            encoding="utf-8",
        )

        problems = dev.validate_benchmark_report(path, 8000, 120)

        for field in (
            "mode",
            "frames",
            "median_frame_ms",
            "p95_frame_ms",
            "median_fps",
            "peak_process_memory_bytes",
            "viewport_width",
            "viewport_height",
            "simulation_cpu_median_ms",
            "simulation_cpu_p95_ms",
        ):
            self.assertTrue(any(field in problem for problem in problems), problems)

    def test_benchmark_accepts_zero_resolution_simulation_cpu_timings(self) -> None:
        dev = load_dev_module()
        path = self.root / "zero-simulation-timing.json"
        path.write_text(
            json.dumps(
                {
                    "mode": "rendered_primitive_movement_only",
                    "requested_soldiers": 8000,
                    "live_soldiers": 8000,
                    "formations": 80,
                    "seconds": 120,
                    "frames": 7200,
                    "median_frame_ms": 12.5,
                    "p95_frame_ms": 18.75,
                    "median_fps": 80.0,
                    "peak_process_memory_bytes": 1073741824,
                    "viewport_width": 1600,
                    "viewport_height": 900,
                    "simulation_cpu_median_ms": 0,
                    "simulation_cpu_p95_ms": 0,
                }
            ),
            encoding="utf-8-sig",
        )

        problems = dev.validate_benchmark_report(path, 8000, 120)

        self.assertEqual(problems, [])

    def test_package_invokes_installed_run_uat_for_mac(self) -> None:
        engine = self.make_engine()

        result = self.run_cli("--engine", str(engine), "package")

        self.assertEqual(result.returncode, 0, result.stdout)
        call = self.read_calls()[0]
        self.assertEqual(call["program"], "RunUAT.sh")
        self.assertEqual(call["argv"][0], "BuildCookRun")
        self.assertIn("-platform=Mac", call["argv"])
        self.assertIn("-clientconfig=Shipping", call["argv"])
        self.assertIn("-archive", call["argv"])

    def test_doctor_writes_exact_unreal_version_without_hardware_identifiers(self) -> None:
        engine = self.make_engine()
        for program in ("cmake", "ctest", "git-lfs"):
            self.install_recorder(self.bin / program)

        self.run_cli("--engine", str(engine), "doctor")

        lock = self.root / "toolchain.lock.json"
        self.assertTrue(lock.is_file())
        report = json.loads(lock.read_text(encoding="utf-8"))
        self.assertEqual(report["unreal"]["version"], "5.8.2")
        self.assertEqual(report["unreal"]["changelist"], 56702186)
        serialized = json.dumps(report).lower()
        self.assertNotIn("serial_number", serialized)
        self.assertNotIn("hardware_uuid", serialized)
        self.assertNotIn("platform_uuid", serialized)

    def test_hardware_profile_parser_keeps_specs_and_drops_identifiers(self) -> None:
        dev = load_dev_module()
        payload = {
            "SPHardwareDataType": [
                {
                    "chip_type": "Apple M1 Max",
                    "number_processors": "proc 10:8:2:0",
                    "physical_memory": "32 GB",
                    "serial_number": "SECRET",
                    "platform_UUID": "SECRET-UUID",
                    "provisioning_UDID": "SECRET-UDID",
                }
            ]
        }

        summary = dev.parse_hardware_profile(payload)

        self.assertEqual(summary["cpu_model"], "Apple M1 Max")
        self.assertEqual(summary["physical_cores"], 10)
        self.assertEqual(summary["logical_cores"], 10)
        self.assertEqual(summary["memory_bytes"], 32 * 1024**3)
        self.assertNotIn("SECRET", json.dumps(summary))

    def test_timeout_returns_124_and_does_not_report_success(self) -> None:
        engine = self.make_engine("time.sleep(2)")

        result = self.run_cli("--engine", str(engine), "run", "--timeout", "0.05")

        self.assertEqual(result.returncode, 124, result.stdout)
        self.assertIn("timed out", result.stdout.lower())


if __name__ == "__main__":
    unittest.main()
