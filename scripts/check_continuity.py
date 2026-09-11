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


def inspect(video: Path) -> dict:
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
    passed = (len(frames) == 300 and first == 210
              and bool(np.all(gap_counts[:210] == 0))
              and bool(np.all(gap_counts[210:] >= 2)))
    return {
        "method": "Fixed mid-gauge ROI, center strip vs neutral background, 20 gray-level contrast threshold",
        "roi_xywh": [377, 200, 100, 100],
        "frames": len(frames),
        "passed": passed,
        "first_visible_gap_zero_based_frame": first,
        "first_visible_gap_time_s": None if first is None else first / 30,
        "gap_rows_frame_209": int(gap_counts[209]),
        "gap_rows_frame_210": int(gap_counts[210]),
        "all_prefracture_frames_connected_in_roi": bool(np.all(gap_counts[:210] == 0)),
        "all_postfracture_frames_have_gap_in_roi": bool(np.all(gap_counts[210:] >= 2)),
        "minimum_postfracture_gap_rows": int(gap_counts[210:].min()),
        "limitation": "Valid only for this fixed camera, neutral background and unoccluded specimen; corroborate with geometry and manual frame inspection.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--report", type=Path, default=Path("artifacts/continuity-qa.json"))
    args = parser.parse_args()
    result = inspect(args.video)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["passed"]:
        raise SystemExit(1)
