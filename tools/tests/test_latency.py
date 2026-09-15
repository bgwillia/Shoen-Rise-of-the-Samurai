import datetime as dt
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPOSITORY = Path(__file__).resolve().parents[2]
LATENCY = REPOSITORY / "tools" / "latency.py"


def load_latency_module():
    spec = importlib.util.spec_from_file_location("shoen_latency", LATENCY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


NOW = dt.datetime(2026, 9, 15, 16, 0, tzinfo=dt.timezone.utc)


def event(
    event_id: str,
    *,
    kind: str = "select",
    source: str = "slate",
    scene_buildings: int = 1,
    start: float = 1.0,
    frame: int = 10,
    status: str = "observed",
    preview_cache: str | None = None,
) -> dict[str, object]:
    input_time = start if source == "slate" else None
    input_frame = frame if source == "slate" else None
    controller_time = None if source == "frame_poll" else start + 1
    controller_frame = None if source == "frame_poll" else frame
    logic_begin = start + 2
    logic_end = start + 5
    observed = status == "observed"
    result: dict[str, object] = {
        "id": event_id,
        "kind": kind,
        "source": source,
        "input_path": "mouse_button" if source == "slate" else source,
        "scene_buildings": scene_buildings,
        "entity_id": 5,
        "input_frame": input_frame,
        "input_receipt_t_ms": input_time,
        "controller_frame": controller_frame,
        "controller_t_ms": controller_time,
        "stages": [
            {"name": "logic_begin", "t_ms": logic_begin, "game_frame": frame},
            {"name": "state_changed", "t_ms": start + 3, "game_frame": frame},
            {"name": "logic_end", "t_ms": logic_end, "game_frame": frame},
        ],
        "visual": {
            "channel": "scene+hud",
            "channels": ["selection", "inspector"],
            "needs_scene": True,
            "needs_hud": True,
            # Readiness may be recorded inside the instrumented logic scope.
            "ready_t_ms": start + 4 if observed else None,
            "ready_frame": frame if observed else None,
            "render_frame": frame + 1 if observed else None,
            "backbuffer_t_ms": start + 12 if observed else None,
            "status": status,
        },
    }
    if preview_cache is not None:
        result["preview_cache"] = preview_cache
    return result


def capture(
    events: list[dict[str, object]],
    *,
    session_id: str = "session-a",
    overflow_count: int = 0,
    captured_at: str = "2026-09-15T15:59:00Z",
    frames: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "endpoint": "backbuffer_ready_rt",
        "clock": "FPlatformTime::Cycles64",
        "seconds_per_cycle": 1e-9,
        "captured_at_utc": captured_at,
        "session": {
            "id": session_id,
            "viewport_width": 1600,
            "viewport_height": 900,
        },
        "event_count": len(events),
        "overflow_count": overflow_count,
        "dropped_event_count": overflow_count,
        "dropped_stage_count": 0,
        "dropped_frame_count": 0,
        "dropped_render_count": 0,
        "frames": frames
        if frames is not None
        else [
            {"scene_buildings": 1, "game_frame": 10, "frame_ms": 10.0},
            {"scene_buildings": 1, "game_frame": 11, "frame_ms": 20.0},
        ],
        "events": events,
    }


class LatencyReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_capture(self, payload: dict[str, object], name: str = "capture.json") -> Path:
        path = self.root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def analyzer(self):
        self.assertTrue(LATENCY.is_file(), "latency analyzer must exist")
        return load_latency_module()

    def test_aggregates_each_interaction_source_count_and_preview_cache_cohort(self) -> None:
        latency = self.analyzer()
        events = [
            event("s1", start=0, scene_buildings=1),
            event("s2", start=20, scene_buildings=1),
            event("s3", start=40, scene_buildings=1),
            event("s4", start=60, scene_buildings=1),
            event("p-hit", kind="preview", source="frame_poll", scene_buildings=10, preview_cache="hit"),
            event("p-miss", kind="preview", source="frame_poll", scene_buildings=10, preview_cache="miss"),
            event("hundred", kind="placement_confirm_success", source="replay", scene_buildings=100),
        ]
        # Give the selection samples distinct logic durations and totals.
        for index, sample in enumerate(events[:4], start=1):
            sample["stages"][2]["t_ms"] = sample["stages"][0]["t_ms"] + index
            sample["visual"]["backbuffer_t_ms"] = sample["input_receipt_t_ms"] + 10 + index
        path = self.write_capture(capture(events))

        report = latency.analyze_files([path], now=NOW)

        self.assertTrue(report["complete"], report["issues"])
        groups = {
            (item["kind"], item["source"], item["scene_buildings"], item["preview_cache"]): item
            for item in report["groups"]
        }
        selected = groups[("select", "slate", 1, None)]
        self.assertEqual(selected["observed_n"], 4)
        self.assertEqual(
            selected["logic_duration_ms"], {"n": 4, "median": 2.5, "p95": 4.0, "max": 4.0}
        )
        self.assertEqual(
            selected["input_to_logic_ms"], {"n": 4, "median": 2.0, "p95": 2.0, "max": 2.0}
        )
        self.assertEqual(
            selected["total_ms"], {"n": 4, "median": 12.5, "p95": 14.0, "max": 14.0}
        )
        self.assertIn(("preview", "frame_poll", 10, "hit"), groups)
        self.assertIn(("preview", "frame_poll", 10, "miss"), groups)
        self.assertIn(("placement_confirm_success", "replay", 100, None), groups)
        self.assertEqual(report["quality"]["events_n"], 7)
        self.assertEqual(report["quality"]["observed_n"], 7)

    def test_input_to_logic_is_reported_only_for_slate_and_total_uses_honest_origin(self) -> None:
        latency = self.analyzer()
        samples = [
            event("slate", source="slate", start=0),
            event("replay", source="replay", start=20),
            event("poll", kind="preview", source="frame_poll", start=40, preview_cache="hit"),
        ]
        report = latency.analyze_files([self.write_capture(capture(samples))], now=NOW)
        groups = {item["source"]: item for item in report["groups"]}

        self.assertEqual(groups["slate"]["input_to_logic_ms"]["median"], 2.0)
        self.assertIsNone(groups["replay"]["input_to_logic_ms"])
        self.assertIsNone(groups["frame_poll"]["input_to_logic_ms"])
        self.assertEqual(groups["replay"]["total_ms"]["median"], 11.0)
        self.assertEqual(groups["frame_poll"]["total_ms"]["median"], 10.0)

    def test_groups_frame_pacing_by_event_level_scene_count(self) -> None:
        latency = self.analyzer()
        frames = [
            {"scene_buildings": 1, "game_frame": 1, "frame_ms": 8.0},
            {"scene_buildings": 10, "game_frame": 2, "frame_ms": 10.0},
            {"scene_buildings": 10, "game_frame": 3, "frame_ms": 30.0},
            {"scene_buildings": 100, "game_frame": 4, "frame_ms": 20.0},
        ]
        report = latency.analyze_files(
            [self.write_capture(capture([event("one")], frames=frames))], now=NOW
        )

        pacing = {item["scene_buildings"]: item for item in report["frame_pacing"]}
        self.assertEqual(pacing[10]["n"], 2)
        self.assertEqual(
            pacing[10]["frame_ms"], {"n": 2, "median": 20.0, "p95": 30.0, "max": 30.0}
        )

    def test_reports_optional_scene_render_thread_decomposition(self) -> None:
        latency = self.analyzer()
        first = event("scene-one", start=0)
        first["visual"]["scene_rt_t_ms"] = 7.0
        second = event("scene-two", start=20)
        # Render-thread work can begin inside the game-thread logic scope.
        second["visual"]["scene_rt_t_ms"] = 24.0

        report = latency.analyze_files(
            [self.write_capture(capture([first, second]))], now=NOW
        )

        self.assertTrue(report["complete"], report["issues"])
        group = report["groups"][0]
        self.assertEqual(
            group["logic_to_scene_rt_ms"],
            {"n": 2, "median": 0.5, "p95": 2.0, "max": 2.0},
        )
        self.assertEqual(
            group["scene_rt_to_backbuffer_ms"],
            {"n": 2, "median": 6.5, "p95": 8.0, "max": 8.0},
        )

        invalid = event("bad-scene-rt", start=40)
        invalid["visual"]["scene_rt_t_ms"] = 41.0
        invalid_report = latency.analyze_files(
            [self.write_capture(capture([invalid]), "invalid-scene-rt.json")], now=NOW
        )
        self.assertFalse(invalid_report["complete"])
        self.assertTrue(
            any("scene_rt_t_ms precedes logic_begin" in issue for issue in invalid_report["issues"]),
            invalid_report["issues"],
        )

    def test_rejects_stale_future_or_wrong_schema_captures(self) -> None:
        latency = self.analyzer()
        cases = [
            (capture([event("a")], captured_at="2026-09-13T00:00:00Z"), "stale"),
            (capture([event("a")], captured_at="2026-09-15T16:10:01Z"), "future"),
            ({**capture([event("a")]), "schema_version": 2}, "schema_version"),
            ({**capture([event("a")]), "endpoint": "screen_scanout"}, "endpoint"),
            ({**capture([event("a")]), "clock": "wall_clock"}, "clock"),
            ({key: value for key, value in capture([event("a")]).items() if key != "event_count"}, "event_count"),
        ]
        for index, (payload, expected) in enumerate(cases):
            with self.subTest(expected=expected):
                report = latency.analyze_files(
                    [self.write_capture(payload, f"invalid-{index}.json")], now=NOW
                )
                self.assertFalse(report["complete"])
                self.assertTrue(any(expected in issue for issue in report["issues"]), report["issues"])

    def test_rejects_bad_stage_order_frames_and_source_association(self) -> None:
        latency = self.analyzer()
        reversed_stages = event("stages")
        reversed_stages["stages"][1]["t_ms"] = 99
        wrong_source = event("source", source="replay")
        wrong_source["input_receipt_t_ms"] = 1.0
        wrong_source["input_frame"] = 1
        wrong_frames = event("frames")
        wrong_frames["visual"]["render_frame"] = 9
        duplicate_stage = event("duplicate")
        duplicate_stage["stages"][1]["name"] = "logic_begin"
        payload = capture([reversed_stages, wrong_source, wrong_frames, duplicate_stage])

        report = latency.analyze_files([self.write_capture(payload)], now=NOW)

        self.assertFalse(report["complete"])
        joined = "\n".join(report["issues"])
        self.assertIn("stage timestamps", joined)
        self.assertIn("non-Slate", joined)
        self.assertIn("render_frame", joined)
        self.assertIn("duplicate stage", joined)

    def test_counts_superseded_but_marks_pending_overflow_and_missing_observations_incomplete(self) -> None:
        latency = self.analyzer()
        observed = event("observed", kind="preview", source="frame_poll", preview_cache="miss")
        superseded = event(
            "superseded", kind="preview", source="frame_poll", preview_cache="miss", status="superseded"
        )
        pending = event("pending", kind="select", status="pending")
        payload = capture([observed, superseded, pending], overflow_count=2)

        report = latency.analyze_files([self.write_capture(payload)], now=NOW)

        self.assertFalse(report["complete"])
        preview = next(item for item in report["groups"] if item["kind"] == "preview")
        self.assertEqual(preview["observed_n"], 1)
        self.assertEqual(preview["superseded_n"], 1)
        self.assertEqual(preview["pending_n"], 0)
        self.assertTrue(any("overflow_count" in issue for issue in report["issues"]), report["issues"])
        self.assertTrue(any("pending" in issue for issue in report["issues"]), report["issues"])

        missing = capture([event("only-superseded", status="superseded")], session_id="session-b")
        missing_report = latency.analyze_files(
            [self.write_capture(missing, "missing.json")], now=NOW
        )
        self.assertFalse(missing_report["complete"])
        self.assertTrue(any("no observed" in issue for issue in missing_report["issues"]), missing_report["issues"])

    def test_optional_dropped_input_count_contributes_to_overflow(self) -> None:
        latency = self.analyzer()
        payload = capture([event("lost-input")])
        payload["dropped_input_count"] = 1
        payload["overflow_count"] = 1

        report = latency.analyze_files([self.write_capture(payload)], now=NOW)

        self.assertFalse(report["complete"])
        self.assertEqual(report["quality"]["overflow_count"], 1)
        self.assertEqual(report["quality"]["dropped_count"], 1)
        self.assertTrue(
            any("dropped_input_count is 1" in issue for issue in report["issues"]),
            report["issues"],
        )

    def test_not_requested_keeps_logic_metrics_without_claiming_visual_latency(self) -> None:
        latency = self.analyzer()
        sample = event("cached", kind="preview", source="frame_poll", preview_cache="hit")
        sample["visual"] = {
            "channel": "none",
            "channels": [],
            "needs_scene": False,
            "needs_hud": False,
            "ready_t_ms": None,
            "ready_frame": None,
            "render_frame": None,
            "backbuffer_t_ms": None,
            "status": "not_requested",
        }

        report = latency.analyze_files([self.write_capture(capture([sample]))], now=NOW)

        self.assertTrue(report["complete"], report["issues"])
        group = report["groups"][0]
        self.assertEqual(group["not_requested_n"], 1)
        self.assertEqual(group["observed_n"], 0)
        self.assertEqual(group["logic_duration_ms"]["median"], 3.0)
        self.assertIsNone(group["logic_to_backbuffer_ready_rt_ms"])
        self.assertIsNone(group["total_ms"])

    def test_duplicate_ids_and_malformed_frame_pacing_are_rejected(self) -> None:
        latency = self.analyzer()
        payload = capture(
            [event("duplicate"), event("duplicate", start=20)],
            frames=[
                {"scene_buildings": 1, "game_frame": 2, "frame_ms": 0},
                {"scene_buildings": 1, "game_frame": 2, "frame_ms": 16.0},
            ],
        )

        report = latency.analyze_files([self.write_capture(payload)], now=NOW)

        self.assertFalse(report["complete"])
        joined = "\n".join(report["issues"])
        self.assertIn("duplicate event id", joined)
        self.assertIn("frame_ms", joined)
        self.assertIn("duplicate game_frame", joined)

    def test_rejects_unknown_source_and_source_timing_after_logic(self) -> None:
        latency = self.analyzer()
        unknown = event("unknown", source="replay")
        unknown["source"] = "timer"
        late = event("late")
        late["controller_t_ms"] = late["stages"][0]["t_ms"] + 1

        report = latency.analyze_files([self.write_capture(capture([unknown, late]))], now=NOW)

        self.assertFalse(report["complete"])
        joined = "\n".join(report["issues"])
        self.assertIn("unknown source", joined)
        self.assertIn("controller timing follows logic_begin", joined)

    def test_rejects_capture_without_events_or_frame_pacing(self) -> None:
        latency = self.analyzer()

        report = latency.analyze_files(
            [self.write_capture(capture([], frames=[]))], now=NOW
        )

        self.assertFalse(report["complete"])
        joined = "\n".join(report["issues"])
        self.assertIn("no interaction events", joined)
        self.assertIn("no frame pacing samples", joined)

    def test_cli_writes_report_and_uses_nonzero_exit_for_incomplete_capture(self) -> None:
        self.analyzer()
        source = self.write_capture(capture([event("pending", status="pending")]))
        output = self.root / "report.json"

        completed = subprocess.run(
            [sys.executable, str(LATENCY), str(source), "--output", str(output), "--now", NOW.isoformat()],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )

        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertTrue(output.is_file())
        report = json.loads(output.read_text(encoding="utf-8"))
        self.assertFalse(report["complete"])
        self.assertNotIn("display_latency", json.dumps(report).lower())


if __name__ == "__main__":
    unittest.main()
