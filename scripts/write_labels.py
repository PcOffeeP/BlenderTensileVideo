"""Write video-level labels from the same input used for rendering."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

LABEL_KEYS = (
    "video_id", "has_fracture", "fracture_time_s", "fracture_mechanism",
    "fracture_site", "special_case", "material_type", "generator_version", "seed",
)


def make_labels(config: dict, contract: dict) -> dict:
    label = {key: config[key] for key in LABEL_KEYS}
    if label["video_id"] != "synthetic_0001":
        raise ValueError("This prototype only supports synthetic_0001")
    if label["has_fracture"] is not True or label["fracture_time_s"] != 7.0:
        raise ValueError("Prototype requires complete separation at 7.0 seconds")
    if (label["fracture_mechanism"], label["fracture_site"], label["special_case"]) != (
        "韧性断裂", "inside_gauge", None
    ):
        raise ValueError("Labels differ from the frozen prototype")
    if contract["contract_version"] != "tensile-vlm/v4.1":
        raise ValueError("Expected tensile-vlm/v4.1 authority")
    for key, enum_key in (("fracture_mechanism", "fracture_mechanisms"),
                          ("fracture_site", "fracture_sites"),
                          ("special_case", "special_cases")):
        if label[key] is not None and label[key] not in contract[enum_key]:
            raise ValueError(f"Illegal contract enum: {key}")
    if label["material_type"] != "金属" or type(label["seed"]) is not int or label["seed"] != 1001:
        raise ValueError("Material and seed differ from the frozen prototype")
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
    if int(probe["streams"][0].get("nb_read_frames", 0)) != 300:
        raise ValueError("Expected 300 readable frames before writing labels")
    output = video.with_suffix(".json")
    output.write_text(json.dumps(label, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
