"""Check encoded media and labels; visual and downstream gates remain separate."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from fractions import Fraction
from pathlib import Path

from write_labels import make_labels


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(config_path: Path, contract_path: Path, output_dir: Path,
             render_evidence: Path | None = None) -> dict:
    config = json.loads(config_path.read_text())
    expected = make_labels(config, json.loads(contract_path.read_text()))
    video = output_dir / f'{expected["video_id"]}.mp4'
    sidecar = video.with_suffix(".json")
    actual = json.loads(sidecar.read_text())
    if actual != expected:
        raise ValueError("JSON differs from rendering config or contains additional fields")
    probe = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
        "-show_streams", "-show_format", "-show_frames", "-of", "json", str(video)
    ]))
    stream = probe["streams"][0]
    frames = probe["frames"]
    fps = float(Fraction(stream["avg_frame_rate"]))
    expected_fps = config["fps"]
    expected_frames = int(config["duration_s"] * expected_fps)
    first_index = config["implementation"]["fracture_frame"] - 1
    last_index = config["implementation"]["last_continuous_frame"] - 1
    checks = {
        "same_stem": video.stem == sidecar.stem == actual["video_id"],
        "json_matches_config_and_contract": True,
        "resolution": (stream["width"], stream["height"]) == (config["resolution_x"], config["resolution_y"]),
        "frame_rate": abs(fps - expected_fps) < 1e-6,
        "frame_count": int(stream["nb_read_frames"]) == expected_frames and len(frames) == expected_frames,
        "duration": abs(float(probe["format"]["duration"]) - config["duration_s"]) < 1 / expected_fps,
    }
    times = [float(frame["best_effort_timestamp_time"]) for frame in frames]
    checks["timeline"] = len(times) == expected_frames and all(abs(t - i / expected_fps) < 1e-5 for i, t in enumerate(times))
    evidence_summary = None
    if render_evidence is None:
        # The original Golden Prototype predates this internal render receipt.
        # Every later video must prove which config and script built its MP4.
        checks["render_provenance"] = expected["video_id"] == "synthetic_0001"
    else:
        evidence = json.loads(render_evidence.read_text())
        script_path = Path(__file__).resolve().parents[1] / evidence["generator_script"]
        checks["render_provenance"] = (
            evidence["schema_version"] == "synthetic-render-evidence/v0.1"
            and evidence["video_id"] == expected["video_id"]
            and evidence["config_sha256"] == sha256(config_path)
            and evidence["generator_script_sha256"] == sha256(script_path)
            and evidence["video_sha256"] == sha256(video)
            and evidence["first_separated_frame"] == config["implementation"]["fracture_frame"]
            and isinstance(evidence["blender_version"], str)
            and bool(evidence["blender_version"].strip())
        )
        evidence_summary = {"path": str(render_evidence), "sha256": sha256(render_evidence)}
    subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(video),
                    "-map", "0:v:0", "-f", "null", "-"], check=True)
    checks["full_decode"] = True
    report = {
        "checks": checks,
        "passed": all(checks.values()),
        "media": {"codec": stream["codec_name"], "pixel_format": stream["pix_fmt"],
                  "fps": fps, "frames": len(frames), "duration_s": probe["format"]["duration"]},
        "target_boundary": {"last_continuous_frame_index": last_index,
                            "last_continuous_timestamp_s": times[last_index] if len(times) > last_index else None,
                            "first_separated_frame_index": first_index,
                            "first_separated_timestamp_s": times[first_index] if len(times) > first_index else None,
                            "note": "These are expected boundary timestamps, not proof of visual separation."},
        "sha256": {str(p): sha256(p) for p in (video, sidecar, config_path, contract_path)},
        "render_evidence": evidence_summary,
        "visual_gate": "Requires rendered-frame inspection and geometry evidence",
        "downstream_import": "Not tested by this validator",
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--render-evidence", type=Path)
    parser.add_argument("--report", type=Path, default=Path("artifacts/media-qa.json"))
    args = parser.parse_args()
    report = validate(args.config, args.contract, args.output_dir, args.render_evidence)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
