"""Measure the visible neck connection in this fixed, centered prototype only.

This is a pixel check of the encoded video, not a general fracture classifier.
The fixed ROI covers mid-gauge and includes neutral background on both sides.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np


def inspect(video: Path, config: dict) -> dict:
    if (config.get("scene_profile_id") != "metal_flat_dogbone_l1_front_v1"
            or config.get("camera_profile") != "front_fixed_v1"
            or (config.get("resolution_x"), config.get("resolution_y")) != (854, 480)):
        raise ValueError("Fixed ROI continuity check only supports the centered L1 front-view scene")
    raw = subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(video), "-vf",
        "crop=100:100:377:200,format=gray", "-f", "rawvideo", "-"
    ])
    frames = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 100, 100)
    background = np.median(np.concatenate((frames[:, :, :12], frames[:, :, -12:]), axis=2), axis=2)
    # The mid-gauge specimen is centered around x=427. A full-width background
    # row through the center strip means the visible neck is interrupted.
    center = frames[:, :, 43:57].max(axis=2).astype(float)
    missing = center < background + 20
    gap_counts = missing.sum(axis=1)
    indices = np.flatnonzero(gap_counts >= 2)
    first = int(indices[0]) if len(indices) else None
    first_expected = config["implementation"]["fracture_frame"] - 1
    last_expected = first_expected - 1
    frame_count = int(config["duration_s"] * config["fps"])
    passed = (len(frames) == frame_count and first == first_expected
              and bool(np.all(gap_counts[:first_expected] == 0))
              and bool(np.all(gap_counts[first_expected:] >= 2)))
    report = {
        "method": "Fixed mid-gauge ROI, center strip vs neutral background, 20 gray-level contrast threshold",
        "roi_xywh": [377, 200, 100, 100],
        "frames": len(frames),
        "passed": passed,
        "expected_first_visible_gap_zero_based_frame": first_expected,
        "first_visible_gap_zero_based_frame": first,
        "first_visible_gap_time_s": None if first is None else first / config["fps"],
        "gap_rows_last_continuous_frame": int(gap_counts[last_expected]),
        "gap_rows_first_separated_frame": int(gap_counts[first_expected]),
        "all_prefracture_frames_connected_in_roi": bool(np.all(gap_counts[:first_expected] == 0)),
        "all_postfracture_frames_have_gap_in_roi": bool(np.all(gap_counts[first_expected:] >= 2)),
        "minimum_postfracture_gap_rows": int(gap_counts[first_expected:].min()),
        "limitation": "Valid only for this fixed camera, neutral background and unoccluded specimen; corroborate with geometry and manual frame inspection.",
    }
    if config["implementation"].get("post_fracture_fixture_motion") == "freeze_at_fracture":
        # The top crosshead is isolated from the specimen in this fixed scene.
        # Track its dark top edge in every decoded frame, rather than trusting
        # fixture keyframes alone. The old, continuously driven video moves it
        # several pixels after f181 and should fail this check.
        fixture_raw = subprocess.check_output([
            "ffmpeg", "-v", "error", "-i", str(video), "-vf",
            "crop=240:90:307:55,format=gray", "-f", "rawvideo", "-"
        ])
        fixture_frames = np.frombuffer(fixture_raw, dtype=np.uint8).reshape(-1, 90, 240)
        top_edges = []
        for fixture_frame in fixture_frames:
            ys = np.flatnonzero(np.any(fixture_frame[:50, 15:225] < 55, axis=1))
            top_edges.append(int(ys[0]) if len(ys) else None)
        post_edges = top_edges[first_expected:]
        stopped = (len(top_edges) == frame_count and all(y is not None for y in post_edges)
                   and max(post_edges) - min(post_edges) <= 1)
        release_end = first_expected + config["implementation"]["local_release_duration_frames"]
        steady_gap_rows = gap_counts[release_end:]
        steady_gap = (len(steady_gap_rows) > 0
                      and int(steady_gap_rows.max() - steady_gap_rows.min()) <= 2)
        report["fixture_stop"] = {
            "passed": stopped and steady_gap,
            "method": "Top crosshead edge in fixed frontal ROI, dark-pixel threshold 55; post-fracture drift at most one encoded pixel; post-release gap variation at most two pixel rows",
            "crosshead_top_y_first_separated": top_edges[first_expected],
            "crosshead_top_y_last_frame": top_edges[-1],
            "post_fracture_crosshead_range_px": None if not all(y is not None for y in post_edges) else max(post_edges) - min(post_edges),
            "post_release_gap_range_rows": None if not len(steady_gap_rows) else int(steady_gap_rows.max() - steady_gap_rows.min()),
        }
        report["passed"] = report["passed"] and stopped and steady_gap
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--config", type=Path, default=Path("configs/synthetic_0001.json"))
    parser.add_argument("--report", type=Path, default=Path("artifacts/continuity-qa.json"))
    args = parser.parse_args()
    result = inspect(args.video, json.loads(args.config.read_text()))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["passed"]:
        raise SystemExit(1)
