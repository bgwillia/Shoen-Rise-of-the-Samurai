#!/usr/bin/env python3
"""Validate and summarize SHŌEN interaction profiling captures.

The render endpoint in these reports is Unreal's BackBufferReadyToPresent callback.
It is a stable engine timestamp, not a measurement of display scanout latency.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
from pathlib import Path
import statistics
import sys
from typing import Any, Iterable


SCHEMA_VERSION = 1
ENDPOINT = "backbuffer_ready_rt"
CLOCK = "FPlatformTime::Cycles64"
VALID_VISUAL_STATUSES = {"observed", "superseded", "pending", "not_requested"}
MAX_FUTURE_SKEW = dt.timedelta(minutes=5)


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _nonnegative_number(value: Any) -> bool:
    return _finite_number(value) and value >= 0


def _nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _parse_time(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(dt.timezone.utc)


def _stats(values: Iterable[float]) -> dict[str, float | int] | None:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return None
    p95_index = max(0, math.ceil(0.95 * len(ordered)) - 1)
    return {
        "n": len(ordered),
        "median": float(statistics.median(ordered)),
        "p95": ordered[p95_index],
        "max": ordered[-1],
    }


def _stage_map(event: dict[str, Any], label: str, issues: list[str]) -> dict[str, dict[str, Any]]:
    stages = event.get("stages")
    if not isinstance(stages, list) or not stages:
        issues.append(f"{label}: stages must be a nonempty array")
        return {}

    result: dict[str, dict[str, Any]] = {}
    previous_time: float | None = None
    previous_frame: int | None = None
    for index, stage in enumerate(stages):
        stage_label = f"{label}: stage {index}"
        if not isinstance(stage, dict):
            issues.append(f"{stage_label} must be an object")
            continue
        name = stage.get("name")
        timestamp = stage.get("t_ms")
        frame = stage.get("game_frame")
        if not isinstance(name, str) or not name:
            issues.append(f"{stage_label} has an invalid name")
            continue
        if name in result:
            issues.append(f"{label}: duplicate stage name {name!r}")
        if not _nonnegative_number(timestamp):
            issues.append(f"{stage_label} t_ms must be finite and nonnegative")
        if not _nonnegative_int(frame):
            issues.append(f"{stage_label} game_frame must be a nonnegative integer")
        if (
            previous_time is not None
            and _nonnegative_number(timestamp)
            and timestamp < previous_time
        ):
            issues.append(f"{label}: stage timestamps are not monotonic")
        if previous_frame is not None and _nonnegative_int(frame) and frame < previous_frame:
            issues.append(f"{label}: stage game frames are not monotonic")
        if _nonnegative_number(timestamp):
            previous_time = float(timestamp)
        if _nonnegative_int(frame):
            previous_frame = frame
        result[name] = stage

    if "logic_begin" not in result or "logic_end" not in result:
        issues.append(f"{label}: stages must contain logic_begin and logic_end")
    elif stages.index(result["logic_begin"]) >= stages.index(result["logic_end"]):
        issues.append(f"{label}: logic_begin must precede logic_end")
    return result


def _validate_visual(
    event: dict[str, Any],
    stages: dict[str, dict[str, Any]],
    label: str,
    issues: list[str],
) -> str | None:
    visual = event.get("visual")
    if not isinstance(visual, dict):
        issues.append(f"{label}: visual must be an object")
        return None
    status = visual.get("status")
    if not isinstance(status, str) or status not in VALID_VISUAL_STATUSES:
        issues.append(f"{label}: invalid visual status {status!r}")
        return None
    channels = visual.get("channels")
    if not isinstance(channels, list) or any(not isinstance(item, str) or not item for item in channels):
        issues.append(f"{label}: visual channels must be an array of nonempty strings")
    for flag in ("needs_scene", "needs_hud"):
        if not isinstance(visual.get(flag), bool):
            issues.append(f"{label}: visual {flag} must be boolean")
    scene_flag, hud_flag = visual.get("needs_scene"), visual.get("needs_hud")
    expected_channel = None
    if isinstance(scene_flag, bool) and isinstance(hud_flag, bool):
        expected_channel = {
            (False, False): "none",
            (True, False): "scene",
            (False, True): "hud",
            (True, True): "scene+hud",
        }[(scene_flag, hud_flag)]
    if expected_channel is not None and visual.get("channel") != expected_channel:
        issues.append(f"{label}: visual channel does not match needs_scene/needs_hud")

    timing_fields = (
        "ready_t_ms",
        "ready_frame",
        "scene_rt_t_ms",
        "render_frame",
        "backbuffer_t_ms",
    )
    if status == "not_requested":
        if visual.get("needs_scene") or visual.get("needs_hud") or channels:
            issues.append(f"{label}: not_requested visual must not require channels")
        if any(visual.get(field) is not None for field in timing_fields):
            issues.append(f"{label}: not_requested visual timestamps and frames must be null")
        return status

    if status in ("observed", "pending", "superseded"):
        if not visual.get("needs_scene") and not visual.get("needs_hud"):
            issues.append(f"{label}: {status} visual must request a scene or HUD update")
        if isinstance(channels, list) and not channels:
            issues.append(f"{label}: {status} visual must name at least one channel")

    scene_rt_time = visual.get("scene_rt_t_ms")
    if scene_rt_time is not None:
        if not _nonnegative_number(scene_rt_time):
            issues.append(f"{label}: scene_rt_t_ms must be finite and nonnegative or null")
        if not visual.get("needs_scene"):
            issues.append(f"{label}: scene_rt_t_ms is only valid for scene updates")
        if status != "observed":
            issues.append(f"{label}: unobserved visual must have null scene_rt_t_ms")

    if status == "observed":
        ready_time = visual.get("ready_t_ms")
        backbuffer_time = visual.get("backbuffer_t_ms")
        ready_frame = visual.get("ready_frame")
        render_frame = visual.get("render_frame")
        if not _nonnegative_number(ready_time):
            issues.append(f"{label}: observed ready_t_ms must be finite and nonnegative")
        if not _nonnegative_number(backbuffer_time):
            issues.append(f"{label}: observed backbuffer_t_ms must be finite and nonnegative")
        if not _nonnegative_int(ready_frame):
            issues.append(f"{label}: observed ready_frame must be a nonnegative integer")
        if not _nonnegative_int(render_frame):
            issues.append(f"{label}: observed render_frame must be a nonnegative integer")
        begin = stages.get("logic_begin", {})
        end = stages.get("logic_end", {})
        begin_time = begin.get("t_ms")
        end_time = end.get("t_ms")
        begin_frame = begin.get("game_frame")
        end_frame = end.get("game_frame")
        if _finite_number(ready_time) and _finite_number(begin_time) and ready_time < begin_time:
            issues.append(f"{label}: ready_t_ms precedes logic_begin")
        if _finite_number(backbuffer_time):
            if _finite_number(ready_time) and backbuffer_time < ready_time:
                issues.append(f"{label}: backbuffer_t_ms precedes ready_t_ms")
            if _finite_number(end_time) and backbuffer_time < end_time:
                issues.append(f"{label}: backbuffer_t_ms precedes logic_end")
        if _finite_number(scene_rt_time):
            if _finite_number(begin_time) and scene_rt_time < begin_time:
                issues.append(f"{label}: scene_rt_t_ms precedes logic_begin")
            if _finite_number(backbuffer_time) and scene_rt_time > backbuffer_time:
                issues.append(f"{label}: scene_rt_t_ms follows backbuffer_t_ms")
        if _nonnegative_int(ready_frame) and _nonnegative_int(begin_frame) and ready_frame < begin_frame:
            issues.append(f"{label}: ready_frame precedes logic_begin frame")
        if _nonnegative_int(render_frame):
            minimum_frames = [value for value in (ready_frame, end_frame) if _nonnegative_int(value)]
            if minimum_frames and render_frame < max(minimum_frames):
                issues.append(f"{label}: render_frame precedes readiness or logic completion")
    return status


def _validate_event(
    event: Any,
    label: str,
    issues: list[str],
) -> tuple[dict[str, Any] | None, dict[str, dict[str, Any]], str | None]:
    if not isinstance(event, dict):
        issues.append(f"{label}: event must be an object")
        return None, {}, None
    for field in ("id", "kind", "source"):
        if not isinstance(event.get(field), str) or not event[field]:
            issues.append(f"{label}: {field} must be a nonempty string")
    if not _nonnegative_int(event.get("scene_buildings")):
        issues.append(f"{label}: scene_buildings must be a nonnegative integer")

    source = event.get("source")
    if source not in ("slate", "replay", "frame_poll"):
        issues.append(f"{label}: unknown source {source!r}")
    entity_id = event.get("entity_id")
    if entity_id is not None and not _nonnegative_int(entity_id):
        issues.append(f"{label}: entity_id must be a nonnegative integer or null")
    input_time = event.get("input_receipt_t_ms")
    input_frame = event.get("input_frame")
    controller_time = event.get("controller_t_ms")
    controller_frame = event.get("controller_frame")
    input_path = event.get("input_path")
    if not isinstance(input_path, str) or not input_path:
        issues.append(f"{label}: input_path must be a nonempty string")
    elif source == "replay" and input_path != "replay":
        issues.append(f"{label}: replay source requires replay input_path")
    elif source == "frame_poll" and input_path != "frame_poll":
        issues.append(f"{label}: frame_poll source requires frame_poll input_path")
    elif source == "slate" and input_path not in ("keyboard", "mouse_button", "cursor_motion", "hud_hitbox"):
        issues.append(f"{label}: invalid Slate input_path {input_path!r}")
    if source == "slate":
        if not _nonnegative_number(input_time) or not _nonnegative_int(input_frame):
            issues.append(f"{label}: Slate source requires input receipt time and frame")
        if not _nonnegative_number(controller_time) or not _nonnegative_int(controller_frame):
            issues.append(f"{label}: Slate source requires controller time and frame")
    else:
        if input_time is not None or input_frame is not None:
            issues.append(f"{label}: non-Slate source must not have input receipt timing")
        if source != "frame_poll" and (
            not _nonnegative_number(controller_time) or not _nonnegative_int(controller_frame)
        ):
            issues.append(f"{label}: source {source!r} requires controller time and frame")
        if source == "frame_poll" and (
            (controller_time is None) != (controller_frame is None)
            or (controller_time is not None and not _nonnegative_number(controller_time))
            or (controller_frame is not None and not _nonnegative_int(controller_frame))
        ):
            issues.append(f"{label}: frame_poll controller timing must be null or a valid pair")
    constructed = event.get("slate_constructed_t_ms")
    if constructed is not None:
        if source != "slate" or not _nonnegative_number(constructed):
            issues.append(f"{label}: slate_constructed_t_ms is only valid for Slate source")
        elif _finite_number(input_time) and constructed > input_time:
            issues.append(f"{label}: slate_constructed_t_ms follows input receipt")

    preview_cache = event.get("preview_cache")
    if preview_cache is not None and preview_cache not in ("hit", "miss"):
        issues.append(f"{label}: preview_cache must be hit, miss, or null")

    stages = _stage_map(event, label, issues)
    begin = stages.get("logic_begin", {})
    begin_time = begin.get("t_ms")
    begin_frame = begin.get("game_frame")
    if _finite_number(controller_time) and _finite_number(begin_time) and controller_time > begin_time:
        issues.append(f"{label}: controller timing follows logic_begin")
    if _nonnegative_int(controller_frame) and _nonnegative_int(begin_frame) and controller_frame > begin_frame:
        issues.append(f"{label}: controller frame follows logic_begin frame")
    if _finite_number(input_time) and _finite_number(controller_time) and input_time > controller_time:
        issues.append(f"{label}: input receipt follows controller timing")
    if _nonnegative_int(input_frame) and _nonnegative_int(controller_frame) and input_frame > controller_frame:
        issues.append(f"{label}: input frame follows controller frame")
    status = _validate_visual(event, stages, label, issues)
    return event, stages, status


def _metric_origin(event: dict[str, Any], stages: dict[str, dict[str, Any]]) -> tuple[float | None, int | None]:
    source = event.get("source")
    if source == "slate":
        return event.get("input_receipt_t_ms"), event.get("input_frame")
    if source == "frame_poll":
        begin = stages.get("logic_begin", {})
        return begin.get("t_ms"), begin.get("game_frame")
    return event.get("controller_t_ms"), event.get("controller_frame")


def _new_group(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": event.get("kind"),
        "source": event.get("source"),
        "scene_buildings": event.get("scene_buildings"),
        "preview_cache": event.get("preview_cache"),
        "observed_n": 0,
        "superseded_n": 0,
        "pending_n": 0,
        "not_requested_n": 0,
        "_input_to_logic_ms": [],
        "_logic_duration_ms": [],
        "_logic_to_backbuffer_ms": [],
        "_logic_to_scene_rt_ms": [],
        "_scene_rt_to_backbuffer_ms": [],
        "_total_ms": [],
        "_input_to_logic_frames": [],
        "_logic_to_backbuffer_frames": [],
        "_total_frames": [],
    }


def _finish_group(group: dict[str, Any]) -> dict[str, Any]:
    group["input_to_logic_ms"] = _stats(group.pop("_input_to_logic_ms"))
    group["logic_duration_ms"] = _stats(group.pop("_logic_duration_ms"))
    group["logic_to_backbuffer_ready_rt_ms"] = _stats(group.pop("_logic_to_backbuffer_ms"))
    group["logic_to_scene_rt_ms"] = _stats(group.pop("_logic_to_scene_rt_ms"))
    group["scene_rt_to_backbuffer_ms"] = _stats(group.pop("_scene_rt_to_backbuffer_ms"))
    group["total_ms"] = _stats(group.pop("_total_ms"))
    group["frame_deltas"] = {
        "input_to_logic_frames": _stats(group.pop("_input_to_logic_frames")),
        "logic_to_backbuffer_ready_rt_frames": _stats(group.pop("_logic_to_backbuffer_frames")),
        "total_frames": _stats(group.pop("_total_frames")),
    }
    return group


def analyze_files(
    paths: Iterable[str | Path],
    *,
    now: dt.datetime | None = None,
    max_age_hours: float = 24.0,
) -> dict[str, Any]:
    now_utc = now or dt.datetime.now(dt.timezone.utc)
    if now_utc.tzinfo is None:
        raise ValueError("now must include a timezone")
    now_utc = now_utc.astimezone(dt.timezone.utc)
    issues: list[str] = []
    sessions: list[dict[str, Any]] = []
    groups: dict[tuple[Any, ...], dict[str, Any]] = {}
    pacing: dict[int, list[float]] = {}
    source_files: list[str] = []
    event_count_total = 0
    overflow_total = 0
    dropped_total = 0

    path_list = [Path(path) for path in paths]
    if not path_list:
        issues.append("no capture files supplied")

    for path in path_list:
        source_files.append(str(path.resolve()))
        prefix = str(path)
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            issues.append(f"{prefix}: cannot read JSON capture: {error}")
            continue
        if not isinstance(payload, dict):
            issues.append(f"{prefix}: capture root must be an object")
            continue
        if payload.get("schema_version") != SCHEMA_VERSION:
            issues.append(f"{prefix}: schema_version must be {SCHEMA_VERSION}")
        if payload.get("endpoint") != ENDPOINT:
            issues.append(f"{prefix}: endpoint must be {ENDPOINT}")
        if payload.get("clock") != CLOCK:
            issues.append(f"{prefix}: clock must be {CLOCK}")
        if not _finite_number(payload.get("seconds_per_cycle")) or payload["seconds_per_cycle"] <= 0:
            issues.append(f"{prefix}: seconds_per_cycle must be finite and positive")

        captured = _parse_time(payload.get("captured_at_utc"))
        if captured is None:
            issues.append(f"{prefix}: captured_at_utc must be an ISO-8601 timestamp with timezone")
        elif captured > now_utc + MAX_FUTURE_SKEW:
            issues.append(f"{prefix}: capture timestamp is in the future")
        elif now_utc - captured > dt.timedelta(hours=max_age_hours):
            issues.append(f"{prefix}: capture is stale (older than {max_age_hours:g} hours)")

        session = payload.get("session")
        if not isinstance(session, dict) or not isinstance(session.get("id"), str) or not session["id"]:
            issues.append(f"{prefix}: session.id must be a nonempty string")
            session = {}
        for dimension in ("viewport_width", "viewport_height"):
            value = session.get(dimension)
            if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value <= 0):
                issues.append(f"{prefix}: session.{dimension} must be a positive integer")
        sessions.append(dict(session))

        required_dropped = (
            "dropped_event_count",
            "dropped_stage_count",
            "dropped_frame_count",
            "dropped_render_count",
        )
        dropped_values: list[int] = []
        dropped_counters_valid = True
        for counter_name in required_dropped:
            counter_value = payload.get(counter_name)
            if not _nonnegative_int(counter_value):
                dropped_counters_valid = False
                issues.append(f"{prefix}: {counter_name} must be a nonnegative integer")
            else:
                dropped_values.append(counter_value)
                dropped_total += counter_value
                if counter_value:
                    issues.append(f"{prefix}: {counter_name} is {counter_value}; capture lost samples")
        input_drops = payload.get("dropped_input_count", 0)
        if not _nonnegative_int(input_drops):
            dropped_counters_valid = False
            issues.append(f"{prefix}: dropped_input_count must be a nonnegative integer")
        else:
            dropped_values.append(input_drops)
            dropped_total += input_drops
            if input_drops:
                issues.append(
                    f"{prefix}: dropped_input_count is {input_drops}; capture lost input samples"
                )

        overflow = payload.get("overflow_count")
        if not _nonnegative_int(overflow):
            issues.append(f"{prefix}: overflow_count must be a nonnegative integer")
        else:
            overflow_total += overflow
            if overflow:
                issues.append(f"{prefix}: overflow_count is {overflow}; capture lost samples")
            if dropped_counters_valid and overflow != sum(dropped_values):
                issues.append(f"{prefix}: overflow_count does not equal the dropped counters")

        events = payload.get("events")
        if not isinstance(events, list):
            issues.append(f"{prefix}: events must be an array")
            events = []
        elif not events:
            issues.append(f"{prefix}: capture has no interaction events")
        event_count = payload.get("event_count")
        if not _nonnegative_int(event_count):
            issues.append(f"{prefix}: event_count must be a nonnegative integer")
        elif event_count != len(events):
            issues.append(f"{prefix}: event_count does not match events array")

        event_ids: set[str] = set()
        for index, raw_event in enumerate(events):
            event_count_total += 1
            event_label = f"{prefix}: event {index}"
            event, stages, status = _validate_event(raw_event, event_label, issues)
            if event is None:
                continue
            event_id = event.get("id")
            if isinstance(event_id, str):
                if event_id in event_ids:
                    issues.append(f"{event_label}: duplicate event id {event_id!r}")
                event_ids.add(event_id)
            if (
                not isinstance(event.get("kind"), str)
                or not isinstance(event.get("source"), str)
                or not _nonnegative_int(event.get("scene_buildings"))
                or event.get("preview_cache") not in (None, "hit", "miss")
            ):
                continue
            key = (
                event.get("kind"),
                event.get("source"),
                event.get("scene_buildings"),
                event.get("preview_cache"),
            )
            group = groups.setdefault(key, _new_group(event))
            if status in VALID_VISUAL_STATUSES:
                group[f"{status}_n"] += 1
            if status == "pending":
                issues.append(f"{event_label}: visual observation is pending")

            # Superseded and pending events cannot support completed duration claims.
            if status not in ("observed", "not_requested"):
                continue
            begin = stages.get("logic_begin", {})
            end = stages.get("logic_end", {})
            begin_t, end_t = begin.get("t_ms"), end.get("t_ms")
            begin_frame, end_frame = begin.get("game_frame"), end.get("game_frame")
            if _finite_number(begin_t) and _finite_number(end_t) and end_t >= begin_t:
                group["_logic_duration_ms"].append(end_t - begin_t)
            if event.get("source") == "slate":
                input_t, input_frame = event.get("input_receipt_t_ms"), event.get("input_frame")
                if _finite_number(input_t) and _finite_number(begin_t) and begin_t >= input_t:
                    group["_input_to_logic_ms"].append(begin_t - input_t)
                if _nonnegative_int(input_frame) and _nonnegative_int(begin_frame) and begin_frame >= input_frame:
                    group["_input_to_logic_frames"].append(begin_frame - input_frame)

            if status == "observed":
                visual = event.get("visual", {})
                backbuffer = visual.get("backbuffer_t_ms")
                scene_rt = visual.get("scene_rt_t_ms")
                render_frame = visual.get("render_frame")
                if _finite_number(backbuffer) and _finite_number(end_t) and backbuffer >= end_t:
                    group["_logic_to_backbuffer_ms"].append(backbuffer - end_t)
                if _nonnegative_int(render_frame) and _nonnegative_int(end_frame) and render_frame >= end_frame:
                    group["_logic_to_backbuffer_frames"].append(render_frame - end_frame)
                if _finite_number(scene_rt) and _finite_number(end_t):
                    group["_logic_to_scene_rt_ms"].append(scene_rt - end_t)
                if _finite_number(scene_rt) and _finite_number(backbuffer) and backbuffer >= scene_rt:
                    group["_scene_rt_to_backbuffer_ms"].append(backbuffer - scene_rt)
                origin_t, origin_frame = _metric_origin(event, stages)
                if _finite_number(backbuffer) and _finite_number(origin_t) and backbuffer >= origin_t:
                    group["_total_ms"].append(backbuffer - origin_t)
                if _nonnegative_int(render_frame) and _nonnegative_int(origin_frame) and render_frame >= origin_frame:
                    group["_total_frames"].append(render_frame - origin_frame)

        frames = payload.get("frames", [])
        if not isinstance(frames, list):
            issues.append(f"{prefix}: frames must be an array")
            frames = []
        elif not frames:
            issues.append(f"{prefix}: capture has no frame pacing samples")
        seen_frames: set[tuple[int, int]] = set()
        for index, frame_record in enumerate(frames):
            frame_label = f"{prefix}: frame {index}"
            if not isinstance(frame_record, dict):
                issues.append(f"{frame_label} must be an object")
                continue
            count = frame_record.get("scene_buildings")
            number = frame_record.get("game_frame")
            duration = frame_record.get("frame_ms")
            if not _nonnegative_int(count):
                issues.append(f"{frame_label}: scene_buildings must be a nonnegative integer")
            if not _nonnegative_int(number):
                issues.append(f"{frame_label}: game_frame must be a nonnegative integer")
            if not _finite_number(duration) or duration <= 0:
                issues.append(f"{frame_label}: frame_ms must be finite and positive")
            if _nonnegative_int(count) and _nonnegative_int(number):
                frame_key = (count, number)
                if frame_key in seen_frames:
                    issues.append(f"{frame_label}: duplicate game_frame {number} for scene count {count}")
                seen_frames.add(frame_key)
            if _nonnegative_int(count) and _finite_number(duration) and duration > 0:
                pacing.setdefault(count, []).append(float(duration))

    for group in groups.values():
        requested = group["observed_n"] + group["superseded_n"] + group["pending_n"]
        if requested and group["observed_n"] == 0:
            issues.append(
                f"group {group['kind']}/{group['source']}/{group['scene_buildings']}: "
                "visual change requested but no observed backbuffer sample"
            )

    finished_groups = [
        _finish_group(group)
        for _, group in sorted(groups.items(), key=lambda item: tuple(str(value) for value in item[0]))
    ]
    frame_pacing = [
        {"scene_buildings": count, "n": len(values), "frame_ms": _stats(values)}
        for count, values in sorted(pacing.items())
    ]
    quality = {
        "events_n": event_count_total,
        "observed_n": sum(group["observed_n"] for group in finished_groups),
        "superseded_n": sum(group["superseded_n"] for group in finished_groups),
        "pending_n": sum(group["pending_n"] for group in finished_groups),
        "not_requested_n": sum(group["not_requested_n"] for group in finished_groups),
        "overflow_count": overflow_total,
        "dropped_count": dropped_total,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "endpoint": ENDPOINT,
        "generated_at_utc": now_utc.isoformat().replace("+00:00", "Z"),
        "source_files": source_files,
        "complete": not issues,
        "issues": issues,
        "sessions": sessions,
        "groups": finished_groups,
        "frame_pacing": frame_pacing,
        "quality": quality,
        "notes": [
            "The endpoint is Unreal BackBufferReadyToPresent, not display scanout.",
            "source=slate identifies the Slate route; it does not prove physical input origin.",
        ],
    }


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("captures", nargs="+", type=Path, help="profiling capture JSON files")
    parser.add_argument("--output", required=True, type=Path, help="output report JSON path")
    parser.add_argument("--max-age-hours", type=float, default=24.0)
    parser.add_argument("--now", help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _argument_parser().parse_args(argv)
    now = _parse_time(args.now) if args.now else None
    if args.now and now is None:
        print("error: --now must be an ISO-8601 timestamp with timezone", file=sys.stderr)
        return 2
    if not _finite_number(args.max_age_hours) or args.max_age_hours <= 0:
        print("error: --max-age-hours must be finite and positive", file=sys.stderr)
        return 2
    report = analyze_files(args.captures, now=now, max_age_hours=args.max_age_hours)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {args.output}")
    if report["complete"]:
        print(f"validated {len(report['groups'])} interaction cohorts")
        return 0
    for issue in report["issues"]:
        print(f"error: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
