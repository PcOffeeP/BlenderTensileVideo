"""Write video-level labels from the same input used for rendering."""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
from pathlib import Path

LABEL_KEYS = (
    "video_id", "has_fracture", "fracture_time_s", "fracture_mechanism",
    "fracture_site", "special_case", "material_type", "generator_version", "seed",
)

MATERIAL_PROFILES_BY_SCENE = {
    "metal_flat_dogbone_l1_front_v1": {
        "金属": {"neutral_brushed_metal_v1"},
    },
    "major_fractures_review_v1": {
        "金属": {"neutral_brushed_metal_v1"},
        "高分子": {"matte_polymer_gray_v1"},
        "复材": {"laminate_composite_neutral_v1"},
    },
}


def make_labels(config: dict, contract: dict) -> dict:
    label = {key: config[key] for key in LABEL_KEYS}
    if not re.fullmatch(r"synthetic_\d{4}", label["video_id"]):
        raise ValueError("Invalid synthetic video_id")
    if label["has_fracture"] is not True or label["special_case"] is not None:
        raise ValueError("v0.1 writer only supports normal videos with a confirmed fracture")
    if (not isinstance(label["fracture_time_s"], (int, float))
            or isinstance(label["fracture_time_s"], bool)
            or not math.isfinite(label["fracture_time_s"])):
        raise ValueError("fracture_time_s must be numeric")
    fps = config["fps"]
    duration = config["duration_s"]
    if (type(fps) is not int or fps <= 0 or not isinstance(duration, (int, float))
            or isinstance(duration, bool) or not math.isfinite(duration) or duration <= 0):
        raise ValueError("Expected positive fps and duration")
    frame_count = duration * fps
    if not float(frame_count).is_integer():
        raise ValueError("Expected positive integer fps and an integral frame count")
    first_separated = config["implementation"]["fracture_frame"]
    if (type(first_separated) is not int or first_separated < 2
            or first_separated > int(frame_count)
            or config["implementation"]["last_continuous_frame"] != first_separated - 1
            or abs(label["fracture_time_s"] - (first_separated - 1) / fps) > 1e-9):
        raise ValueError("Fracture time must equal the first separated frame timestamp")
    if contract["contract_version"] != "tensile-vlm/v4.1":
        raise ValueError("Expected tensile-vlm/v4.1 authority")
    for key, enum_key in (("fracture_mechanism", "fracture_mechanisms"),
                          ("fracture_site", "fracture_sites"),
                          ("special_case", "special_cases")):
        if label[key] is None and key != "special_case":
            raise ValueError(f"Normal fracture requires {key}")
        if label[key] is not None and label[key] not in contract[enum_key]:
            raise ValueError(f"Illegal contract enum: {key}")
    material_profiles = MATERIAL_PROFILES_BY_SCENE.get(config.get("scene_profile_id"), {})
    if config.get("material_profile") not in material_profiles.get(label["material_type"], set()):
        raise ValueError("Material label must match the frozen scene and material profile")
    if type(label["seed"]) is not int or label["seed"] < 0:
        raise ValueError("seed must be a nonnegative integer")
    if not re.fullmatch(r"blender-tensile/v\d+\.\d+", label["generator_version"]):
        raise ValueError("Invalid generator_version")
    return {"schema_version": "synthetic-tensile-video/v0.1", **label}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    args = parser.parse_args()
    label = make_labels(json.loads(args.config.read_text()), json.loads(args.contract.read_text()))
    video = args.output_dir / f'{label["video_id"]}.mp4'
    if not video.is_file() or video.stat().st_size == 0:
        raise ValueError("Render the video successfully before writing labels")
    probe = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
        "-show_entries", "stream=nb_read_frames", "-of", "json", str(video)
    ]))
    config = json.loads(args.config.read_text())
    expected_frames = int(config["duration_s"] * config["fps"])
    if int(probe["streams"][0].get("nb_read_frames", 0)) != expected_frames:
        raise ValueError(f"Expected {expected_frames} readable frames before writing labels")
    output = video.with_suffix(".json")
    output.write_text(json.dumps(label, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
