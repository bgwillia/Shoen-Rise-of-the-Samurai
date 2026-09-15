#!/usr/bin/env python3
"""Reproducible developer commands for the SHŌEN foundation milestone."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from typing import Any, Iterable, Mapping, Sequence
import uuid


DEFAULT_ENGINE_ROOT = Path("/Users/Shared/Epic Games/UE_5.8")
FOUNDATION_MAP = "/Game/Domain/Maps/Foundation"
FOUNDATION_TEST = "Shoen.Foundation"
AUTOMATION_TEST_PREFIXES = {
    "foundation": FOUNDATION_TEST,
    "placement": "Shoen.Placement",
    "inspection": "Shoen.Inspection",
}
BENCHMARK_SOLDIER_COUNTS = (1000, 4000, 8000, 20000)
RENDERED_WINDOW_ARGUMENTS = ("-windowed", "-ResX=1600", "-ResY=900", "-NoVSync")
TIMEOUT_EXIT_CODE = 124


def repository_root(environment: Mapping[str, str]) -> Path:
    override = environment.get("SHOEN_REPO_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parents[1]


def argument_array(arguments: Sequence[os.PathLike[str] | str]) -> list[str]:
    return [os.fspath(argument) for argument in arguments]


def printed_command(arguments: Sequence[os.PathLike[str] | str]) -> str:
    return "+ " + json.dumps(argument_array(arguments), ensure_ascii=False)


def write_log(log_path: Path, message: str, *, append: bool = True) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with log_path.open(mode, encoding="utf-8") as stream:
        stream.write(message)
        if message and not message.endswith("\n"):
            stream.write("\n")


def run_command(
    arguments: Sequence[os.PathLike[str] | str],
    *,
    cwd: Path,
    log_path: Path,
    timeout: float | None,
) -> int:
    argv = argument_array(arguments)
    command_line = printed_command(argv)
    print(command_line, flush=True)
    write_log(log_path, command_line)
    try:
        completed = subprocess.run(
            argv,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired as error:
        output = error.stdout or ""
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        if output:
            print(output, end="" if output.endswith("\n") else "\n")
            write_log(log_path, output)
        message = f"ERROR: command timed out after {timeout:g} seconds"
        print(message, file=sys.stderr)
        write_log(log_path, message)
        return TIMEOUT_EXIT_CODE
    except OSError as error:
        message = f"ERROR: could not start {argv[0]}: {error}"
        print(message, file=sys.stderr)
        write_log(log_path, message)
        return 127

    if completed.stdout:
        print(completed.stdout, end="" if completed.stdout.endswith("\n") else "\n")
        write_log(log_path, completed.stdout)
    if completed.returncode:
        write_log(log_path, f"ERROR: command exited with status {completed.returncode}")
    return completed.returncode


def resolve_program(name: str) -> str | None:
    return shutil.which(name)


def resolve_engine_root(explicit: str | None, environment: Mapping[str, str]) -> Path:
    configured = explicit or environment.get("UE_ROOT")
    return Path(configured).expanduser().resolve() if configured else DEFAULT_ENGINE_ROOT


def editor_executable(engine_root: Path) -> Path:
    return (
        engine_root
        / "Engine"
        / "Binaries"
        / "Mac"
        / "UnrealEditor.app"
        / "Contents"
        / "MacOS"
        / "UnrealEditor"
    )


def build_script(engine_root: Path) -> Path:
    return engine_root / "Engine" / "Build" / "BatchFiles" / "Mac" / "Build.sh"


def run_uat_script(engine_root: Path) -> Path:
    return engine_root / "Engine" / "Build" / "BatchFiles" / "RunUAT.sh"


def require_file(path: Path, description: str) -> bool:
    if path.is_file():
        return True
    print(f"ERROR: {description} not found at {path}", file=sys.stderr)
    return False


def require_engine(engine_root: Path, required_file: Path, description: str) -> bool:
    if not engine_root.is_dir():
        print(f"ERROR: Unreal Engine root not found at {engine_root}", file=sys.stderr)
        return False
    return require_file(required_file, description)


def prepare_log(root: Path, name: str) -> Path:
    path = root / "artifacts" / f"tooling-{name}.log"
    write_log(path, "", append=False)
    return path


def command_core_test(args: argparse.Namespace, root: Path) -> int:
    cmake = resolve_program("cmake")
    ctest = resolve_program("ctest")
    missing = [name for name, path in (("cmake", cmake), ("ctest", ctest)) if path is None]
    if missing:
        print(f"ERROR: required core tool(s) not found on PATH: {', '.join(missing)}", file=sys.stderr)
        return 2

    source = root / "core"
    cmake_lists = source / "CMakeLists.txt"
    if not require_file(cmake_lists, "portable core CMakeLists.txt"):
        return 2
    build = root / "build" / "core"
    log = prepare_log(root, "core-test")
    commands: list[list[str]] = [
        [cmake, "-S", str(source), "-B", str(build), "-DCMAKE_BUILD_TYPE=Debug"],
        [cmake, "--build", str(build), "--config", "Debug"],
        [
            ctest,
            "--test-dir",
            str(build),
            "-C",
            "Debug",
            "--output-on-failure",
            "--no-tests=error",
        ],
    ]
    if args.suite:
        commands[-1].extend(("-R", args.suite))
    for command in commands:
        status = run_command(command, cwd=root, log_path=log, timeout=args.timeout)
        if status:
            return status
    return 0


def command_build(args: argparse.Namespace, root: Path, environment: Mapping[str, str]) -> int:
    engine = resolve_engine_root(args.engine, environment)
    script = build_script(engine)
    if not require_engine(engine, script, "Unreal Engine Mac build script"):
        return 2
    project = root / "game" / "Shoen.uproject"
    if not require_file(project, "Shoen Unreal project"):
        return 2
    log = prepare_log(root, "build")
    return run_command(
        [
            script,
            "ShoenEditor",
            "Mac",
            "Development",
            project,
            "-WaitMutex",
            "-NoHotReloadFromIDE",
        ],
        cwd=root,
        log_path=log,
        timeout=args.timeout,
    )


def editor_base(root: Path, engine: Path) -> tuple[Path, Path] | None:
    editor = editor_executable(engine)
    if not require_engine(engine, editor, "Unreal Editor executable"):
        return None
    project = root / "game" / "Shoen.uproject"
    if not require_file(project, "Shoen Unreal project"):
        return None
    return editor, project


def command_create_map(args: argparse.Namespace, root: Path, environment: Mapping[str, str]) -> int:
    engine = resolve_engine_root(args.engine, environment)
    resolved = editor_base(root, engine)
    if resolved is None:
        return 2
    editor, project = resolved
    generator = root / "tools" / "create_foundation.py"
    if not require_file(generator, "foundation map generator"):
        return 2
    log = prepare_log(root, "create-map")
    status = run_command(
        [
            editor,
            project,
            f"-ExecutePythonScript={generator}",
            "-unattended",
            "-nop4",
            "-nosplash",
            "-NullRHI",
            "-stdout",
            "-FullStdOutLogOutput",
        ],
        cwd=root,
        log_path=log,
        timeout=args.timeout,
    )
    if status:
        return status
    map_file = root / "game" / "Content" / "Domain" / "Maps" / "Foundation.umap"
    if not map_file.is_file() or map_file.stat().st_size == 0:
        message = f"ERROR: editor completed without creating a nonempty map at {map_file}"
        print(message, file=sys.stderr)
        write_log(log, message)
        return 3
    return 0


def report_directory(root: Path, prefix: str) -> Path:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return root / "artifacts" / f"tooling-{prefix}-{stamp}-{uuid.uuid4().hex[:8]}"


def _test_name(record: Mapping[str, Any]) -> str | None:
    for key in ("fullTestPath", "testDisplayName", "testName", "name"):
        value = record.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _automation_records(value: Any) -> Iterable[Mapping[str, Any]]:
    if isinstance(value, dict):
        state = value.get("state") or value.get("status") or value.get("result")
        if isinstance(state, str) and _test_name(value):
            yield value
        for nested in value.values():
            yield from _automation_records(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _automation_records(nested)


def parse_automation_report(report: Path, required_prefix: str) -> tuple[list[Mapping[str, Any]], list[str]]:
    json_files = sorted(report.rglob("*.json")) if report.is_dir() else []
    if not json_files:
        return [], [f"automation report JSON is missing from {report}"]
    records: list[Mapping[str, Any]] = []
    parse_errors: list[str] = []
    for path in json_files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            parse_errors.append(f"could not parse automation report {path}: {error}")
            continue
        records.extend(_automation_records(payload))
    if parse_errors:
        return records, parse_errors
    matching = [record for record in records if (_test_name(record) or "").lower().startswith(required_prefix.lower())]
    if not matching:
        return [], [f"automation report contained no tests matching {required_prefix}"]
    problems: list[str] = []
    accepted = {"success", "succeeded", "pass", "passed"}
    for record in matching:
        name = _test_name(record) or "unnamed test"
        state = str(record.get("state") or record.get("status") or record.get("result") or "Missing")
        errors = record.get("errors", 0)
        error_count = len(errors) if isinstance(errors, list) else errors
        if state.lower() not in accepted or (isinstance(error_count, (int, float)) and error_count > 0):
            problems.append(f"{name}: {state} (errors={error_count})")
    return matching, problems


def command_editor_test(args: argparse.Namespace, root: Path, environment: Mapping[str, str]) -> int:
    engine = resolve_engine_root(args.engine, environment)
    resolved = editor_base(root, engine)
    if resolved is None:
        return 2
    editor, project = resolved
    test_prefix = AUTOMATION_TEST_PREFIXES[args.suite]
    report = report_directory(root, f"editor-test-{args.suite}")
    log = prepare_log(root, f"editor-test-{args.suite}")
    status = run_command(
        [
            editor,
            project,
            f"-ExecCmds=Automation RunTests {test_prefix}",
            "-TestExit=Automation Test Queue Empty",
            "-unattended",
            "-NullRHI",
            f"-ReportExportPath={report}",
            "-nop4",
            "-nosplash",
            "-stdout",
            "-FullStdOutLogOutput",
        ],
        cwd=root,
        log_path=log,
        timeout=args.timeout,
    )
    if status:
        return status
    tests, problems = parse_automation_report(report, test_prefix)
    if problems:
        for problem in problems:
            print(f"ERROR: {problem}", file=sys.stderr)
            write_log(log, f"ERROR: {problem}")
        return 3
    print(f"{len(tests)} automation test passed from {test_prefix}")
    return 0


def command_run(args: argparse.Namespace, root: Path, environment: Mapping[str, str]) -> int:
    engine = resolve_engine_root(args.engine, environment)
    resolved = editor_base(root, engine)
    if resolved is None:
        return 2
    editor, project = resolved
    command: list[os.PathLike[str] | str] = [
        editor,
        project,
        FOUNDATION_MAP,
        "-game",
        *RENDERED_WINDOW_ARGUMENTS,
        f"-ShoenScenario={args.scenario}",
        "-stdout",
        "-FullStdOutLogOutput",
    ]
    if args.soldiers is not None:
        command.append(f"-ShoenSoldiers={args.soldiers}")
    log = prepare_log(root, f"run-{args.scenario}")
    return run_command(command, cwd=root, log_path=log, timeout=args.timeout)


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    parsed = float(value)
    return parsed if math.isfinite(parsed) else None


def validate_benchmark_report(path: Path, soldiers: int, seconds: float) -> list[str]:
    if not path.is_file():
        return [f"benchmark report file was not created at {path}"]
    try:
        report = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return [f"benchmark report is not valid JSON: {error}"]
    if not isinstance(report, dict):
        return ["benchmark report root must be an object"]
    problems: list[str] = []
    if report.get("mode") != "rendered_primitive_movement_only":
        problems.append(
            "mode expected 'rendered_primitive_movement_only', "
            f"got {report.get('mode')!r}"
        )
    expected = {
        "requested_soldiers": soldiers,
        "live_soldiers": soldiers,
        "formations": soldiers // 100,
    }
    for field, wanted in expected.items():
        actual = _number(report.get(field))
        if actual != wanted:
            problems.append(f"{field} expected {wanted}, got {report.get(field)!r}")
    actual_seconds = _number(report.get("seconds"))
    if actual_seconds is None or actual_seconds < seconds:
        problems.append(f"seconds expected at least {seconds:g}, got {report.get('seconds')!r}")
    frames = _number(report.get("frames"))
    if frames is None or frames <= 0 or not frames.is_integer():
        problems.append(f"frames expected a positive integer, got {report.get('frames')!r}")
    median_frame = _number(report.get("median_frame_ms"))
    if median_frame is None or median_frame <= 0:
        problems.append(
            f"median_frame_ms expected a finite positive value, got {report.get('median_frame_ms')!r}"
        )
    p95_frame = _number(report.get("p95_frame_ms"))
    if p95_frame is None or p95_frame <= 0 or (median_frame is not None and p95_frame < median_frame):
        problems.append(
            "p95_frame_ms expected a finite value at least median_frame_ms, "
            f"got {report.get('p95_frame_ms')!r}"
        )
    median_fps = _number(report.get("median_fps"))
    if median_fps is None or median_fps <= 0:
        problems.append(f"median_fps expected a finite positive value, got {report.get('median_fps')!r}")
    for field in ("peak_process_memory_bytes", "viewport_width", "viewport_height"):
        actual = _number(report.get(field))
        if actual is None or actual <= 0:
            problems.append(f"{field} expected a finite positive value, got {report.get(field)!r}")
    simulation_median = _number(report.get("simulation_cpu_median_ms"))
    if simulation_median is None or simulation_median < 0:
        problems.append(
            "simulation_cpu_median_ms expected a finite nonnegative value, "
            f"got {report.get('simulation_cpu_median_ms')!r}"
        )
    simulation_p95 = _number(report.get("simulation_cpu_p95_ms"))
    if (
        simulation_p95 is None
        or simulation_p95 < 0
        or (simulation_median is not None and simulation_p95 < simulation_median)
    ):
        problems.append(
            "simulation_cpu_p95_ms expected a finite nonnegative value at least "
            f"simulation_cpu_median_ms, got {report.get('simulation_cpu_p95_ms')!r}"
        )
    return problems


def command_benchmark(args: argparse.Namespace, root: Path, environment: Mapping[str, str]) -> int:
    engine = resolve_engine_root(args.engine, environment)
    resolved = editor_base(root, engine)
    if resolved is None:
        return 2
    editor, project = resolved
    report = report_directory(root, f"benchmark-{args.soldiers}").with_suffix(".json")
    log = prepare_log(root, f"benchmark-{args.soldiers}")
    seconds_flag = f"{args.seconds:g}"
    status = run_command(
        [
            editor,
            project,
            FOUNDATION_MAP,
            "-game",
            *RENDERED_WINDOW_ARGUMENTS,
            "-ShoenScenario=scale_lab",
            f"-ShoenBenchmarkSeconds={seconds_flag}",
            f"-ShoenSoldiers={args.soldiers}",
            f"-ShoenBenchmarkOutput={report}",
            "-stdout",
            "-FullStdOutLogOutput",
        ],
        cwd=root,
        log_path=log,
        timeout=args.timeout,
    )
    if status:
        return status
    problems = validate_benchmark_report(report, args.soldiers, args.seconds)
    if problems:
        for problem in problems:
            print(f"ERROR: {problem}", file=sys.stderr)
            write_log(log, f"ERROR: {problem}")
        return 3
    print(f"validated benchmark report: {report}")
    return 0


def command_package(args: argparse.Namespace, root: Path, environment: Mapping[str, str]) -> int:
    engine = resolve_engine_root(args.engine, environment)
    script = run_uat_script(engine)
    if not require_engine(engine, script, "installed Unreal Automation Tool script"):
        return 2
    project = root / "game" / "Shoen.uproject"
    if not require_file(project, "Shoen Unreal project"):
        return 2
    output = Path(args.output).expanduser()
    if not output.is_absolute():
        output = (root / output).resolve()
    log = prepare_log(root, "package")
    return run_command(
        [
            script,
            "BuildCookRun",
            f"-project={project}",
            "-noP4",
            "-platform=Mac",
            "-clientconfig=Shipping",
            "-build",
            "-cook",
            "-stage",
            "-pak",
            "-archive",
            f"-archivedirectory={output}",
            "-utf8output",
        ],
        cwd=root,
        log_path=log,
        timeout=args.timeout,
    )


def probe(arguments: Sequence[str]) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            list(arguments),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=20,
            check=False,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return 127, str(error)
    return completed.returncode, completed.stdout.strip()


def first_line(text: str) -> str | None:
    return text.splitlines()[0].strip() if text.strip() else None


def sysctl_value(name: str) -> str | None:
    status, output = probe(["/usr/sbin/sysctl", "-n", name])
    return output if status == 0 and output else None


def tool_version(program: str, version_arguments: Sequence[str]) -> dict[str, Any]:
    path = resolve_program(program)
    if not path:
        return {"available": False, "path": None, "version": None}
    status, output = probe([path, *version_arguments])
    return {"available": status == 0, "path": path, "version": first_line(output)}


def unreal_version(engine: Path) -> dict[str, Any]:
    path = engine / "Engine" / "Build" / "Build.version"
    result: dict[str, Any] = {
        "available": False,
        "root": str(engine),
        "editor": str(editor_executable(engine)),
        "version": None,
        "changelist": None,
        "compatible_changelist": None,
        "branch": None,
    }
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        version = ".".join(str(value[key]) for key in ("MajorVersion", "MinorVersion", "PatchVersion"))
    except (KeyError, OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
        return result
    result.update(
        {
            "available": editor_executable(engine).is_file(),
            "version": version,
            "changelist": value.get("Changelist"),
            "compatible_changelist": value.get("CompatibleChangelist"),
            "branch": value.get("BranchName"),
        }
    )
    return result


def gpu_summary() -> list[dict[str, Any]]:
    profiler = "/usr/sbin/system_profiler"
    status, output = probe([profiler, "SPDisplaysDataType", "-json"])
    if status or not output:
        return []
    try:
        payload = json.loads(output)
    except json.JSONDecodeError:
        return []
    displays = payload.get("SPDisplaysDataType", [])
    result: list[dict[str, Any]] = []
    for display in displays if isinstance(displays, list) else []:
        if not isinstance(display, dict):
            continue
        model = display.get("sppci_model") or display.get("_name") or display.get("spdisplays_chipset-model")
        cores = display.get("sppci_cores") or display.get("spdisplays_gmux-version")
        if model:
            result.append({"model": str(model), "cores": str(cores) if cores else None})
    return result


def os_summary() -> dict[str, Any]:
    values: dict[str, Any] = {"system": platform.system(), "architecture": platform.machine()}
    for field, flag in (
        ("product_name", "-productName"),
        ("version", "-productVersion"),
        ("build", "-buildVersion"),
    ):
        status, output = probe(["/usr/bin/sw_vers", flag])
        values[field] = output if status == 0 and output else None
    return values


def parse_hardware_profile(payload: Mapping[str, Any]) -> dict[str, Any]:
    hardware = payload.get("SPHardwareDataType", [])
    record = hardware[0] if isinstance(hardware, list) and hardware and isinstance(hardware[0], dict) else {}
    processor_text = record.get("number_processors")
    cores: int | None = None
    if isinstance(processor_text, str):
        fields = processor_text.split()
        if len(fields) >= 2:
            cores = _integer_or_none(fields[1].split(":", 1)[0])
    memory_bytes: int | None = None
    memory_text = record.get("physical_memory")
    if isinstance(memory_text, str):
        fields = memory_text.split()
        if len(fields) == 2:
            try:
                quantity = float(fields[0])
            except ValueError:
                quantity = 0
            multipliers = {"KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}
            multiplier = multipliers.get(fields[1].upper())
            if quantity > 0 and multiplier:
                memory_bytes = int(quantity * multiplier)
    return {
        "cpu_model": str(record["chip_type"]) if record.get("chip_type") else None,
        "physical_cores": cores,
        "logical_cores": cores,
        "memory_bytes": memory_bytes,
    }


def hardware_profile() -> dict[str, Any]:
    status, output = probe(["/usr/sbin/system_profiler", "SPHardwareDataType", "-json"])
    if status or not output:
        return parse_hardware_profile({})
    try:
        payload = json.loads(output)
    except json.JSONDecodeError:
        return parse_hardware_profile({})
    return parse_hardware_profile(payload)


def command_doctor(args: argparse.Namespace, root: Path, environment: Mapping[str, str]) -> int:
    engine = resolve_engine_root(args.engine, environment)
    clang_status, clang_output = probe(["/usr/bin/xcrun", "clang", "--version"])
    metal_status, metal_output = probe(["/usr/bin/xcrun", "metal", "--version"])
    memory = sysctl_value("hw.memsize")
    hardware = hardware_profile()
    report: dict[str, Any] = {
        "schema_version": 1,
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "host": {
            "os": os_summary(),
            "cpu": {
                "model": sysctl_value("machdep.cpu.brand_string") or hardware["cpu_model"] or platform.processor() or None,
                "physical_cores": _integer_or_none(sysctl_value("hw.physicalcpu")) or hardware["physical_cores"],
                "logical_cores": _integer_or_none(sysctl_value("hw.logicalcpu")) or hardware["logical_cores"],
            },
            "gpu": gpu_summary(),
            "memory_bytes": _integer_or_none(memory) or hardware["memory_bytes"],
        },
        "unreal": unreal_version(engine),
        "tools": {
            "cmake": tool_version("cmake", ("--version",)),
            "ctest": tool_version("ctest", ("--version",)),
            "git_lfs": tool_version("git-lfs", ("version",)),
            "clang": {
                "available": clang_status == 0,
                "path": "/usr/bin/xcrun clang",
                "version": first_line(clang_output),
            },
            "metal": {
                "available": metal_status == 0,
                "path": "/usr/bin/xcrun metal",
                "version": first_line(metal_output),
            },
        },
    }
    lock = root / "toolchain.lock.json"
    lock.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    unavailable = [
        "Unreal Editor" if not report["unreal"]["available"] else None,
        *[
            name
            for name, details in report["tools"].items()
            if not details.get("available")
        ],
    ]
    missing = [name for name in unavailable if name]
    if missing:
        print(f"ERROR: unavailable required tool(s): {', '.join(missing)}", file=sys.stderr)
        return 2
    return 0


def _integer_or_none(value: str | None) -> int | None:
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


def positive_integer(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def add_timeout(parser: argparse.ArgumentParser, default: float | None) -> None:
    parser.add_argument(
        "--timeout",
        type=positive_float,
        default=default,
        help="maximum child-process runtime in seconds",
    )


def add_engine_override(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--engine",
        default=argparse.SUPPRESS,
        help="override the Unreal Engine root for this command",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--engine",
        help=f"Unreal Engine root (default: UE_ROOT or {DEFAULT_ENGINE_ROOT})",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    doctor = subcommands.add_parser("doctor", help="audit the local build toolchain")
    add_engine_override(doctor)

    core = subcommands.add_parser("core-test", help="configure, build, and test the portable core")
    add_engine_override(core)
    core.add_argument("--suite", help="optional CTest regular-expression filter")
    add_timeout(core, 900)

    build = subcommands.add_parser("build", help="build the ShoenEditor Unreal target")
    add_engine_override(build)
    add_timeout(build, 3600)

    create_map = subcommands.add_parser("create-map", help="generate the Foundation map in Unreal")
    add_engine_override(create_map)
    add_timeout(create_map, 900)

    editor_test = subcommands.add_parser("editor-test", help="run Unreal automation tests")
    add_engine_override(editor_test)
    editor_test.add_argument(
        "--suite",
        choices=tuple(AUTOMATION_TEST_PREFIXES),
        default="foundation",
    )
    add_timeout(editor_test, 1800)

    run = subcommands.add_parser("run", help="run a rendered foundation scenario")
    add_engine_override(run)
    run.add_argument(
        "--scenario",
        choices=("foundation", "scale_lab", "settlement"),
        default="foundation",
    )
    run.add_argument("--soldiers", type=positive_integer)
    add_timeout(run, None)

    benchmark = subcommands.add_parser("benchmark", help="run and validate a rendered scale benchmark")
    add_engine_override(benchmark)
    benchmark.add_argument("--soldiers", type=int, choices=BENCHMARK_SOLDIER_COUNTS, required=True)
    benchmark.add_argument("--seconds", type=positive_float, default=120)
    add_timeout(benchmark, 900)

    package = subcommands.add_parser("package", help="package a Shipping Mac build with installed RunUAT")
    add_engine_override(package)
    package.add_argument("--output", default="build/package")
    add_timeout(package, 7200)
    return parser


def main(argv: Sequence[str] | None = None, environment: Mapping[str, str] | None = None) -> int:
    environment = os.environ if environment is None else environment
    args = build_parser().parse_args(argv)
    root = repository_root(environment)
    if args.command == "doctor":
        return command_doctor(args, root, environment)
    if args.command == "core-test":
        return command_core_test(args, root)
    if args.command == "build":
        return command_build(args, root, environment)
    if args.command == "create-map":
        return command_create_map(args, root, environment)
    if args.command == "editor-test":
        return command_editor_test(args, root, environment)
    if args.command == "run":
        return command_run(args, root, environment)
    if args.command == "benchmark":
        return command_benchmark(args, root, environment)
    if args.command == "package":
        return command_package(args, root, environment)
    raise AssertionError(f"unhandled command {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
