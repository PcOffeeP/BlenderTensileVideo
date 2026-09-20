"""Validate the six-video major-fracture review batch as one unit."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from validate_output import validate


IDS = tuple(f"synthetic_{index:04d}" for index in range(3, 9))
KEYFRAME_NAMES = (
    "initial_f001.png",
    "precursor.png",
    "prefracture.png",
    "first_separation.png",
    "stable_postfracture.png",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument(
        "--batch-dir",
        type=Path,
        default=Path("artifacts/review_batches/major_fractures_v1"),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("artifacts/review_batches/major_fractures_v1/batch-qa.json"),
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    results: dict[str, dict] = {}
    mechanisms: set[str] = set()
    sites: set[str] = set()
    seeds: set[int] = set()
    review_cases: set[str] = set()
    generator_hashes: set[str] = set()
    generator_scripts: set[str] = set()

    for video_id in IDS:
        config_path = root / "configs" / f"{video_id}.json"
        output_dir = args.batch_dir / video_id
        evidence_path = output_dir / "render-evidence.json"
        report = validate(config_path, args.contract, output_dir, evidence_path)
        config = json.loads(config_path.read_text(encoding="utf-8"))
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        mechanisms.add(config["fracture_mechanism"])
        sites.add(config["fracture_site"])
        seeds.add(config["seed"])
        review_cases.add(config["implementation"]["review_case"])
        generator_hashes.add(evidence["generator_script_sha256"])
        generator_scripts.add(evidence["generator_script"])

        keyframes = {
            name: {
                "path": str(output_dir / name),
                "sha256": sha256(output_dir / name),
            }
            for name in KEYFRAME_NAMES
            if (output_dir / name).is_file()
        }
        keyframes_present = len(keyframes) == len(KEYFRAME_NAMES)
        report["checks"]["keyframe_evidence_present"] = keyframes_present
        report["keyframes"] = keyframes
        report["passed"] = report["passed"] and keyframes_present
        results[video_id] = report

        per_video = output_dir / "media-qa.json"
        per_video.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    expected_mechanisms = {
        "韧性断裂",
        "脆性断裂",
        "界面脱粘",
        "爆炸性断裂",
        "半脆半韧断裂",
    }
    expected_sites = {"inside_gauge", "outside_gauge_non_root", "grip_root"}
    coverage = {
        "all_five_fracture_mechanisms": mechanisms == expected_mechanisms,
        "all_three_fracture_sites": sites == expected_sites,
        "six_unique_seeds": len(seeds) == len(IDS),
        "six_distinct_behavior_configs": len(review_cases) == len(IDS),
        "render_provenance_complete": all(
            item["checks"]["render_provenance"] for item in results.values()
        ),
    }
    batch = {
        "schema_version": "major-fracture-review-qa/v0.1",
        "video_ids": list(IDS),
        "coverage": {
            "mechanisms": sorted(mechanisms),
            "sites": sorted(sites),
            "seeds": sorted(seeds),
            "review_cases": sorted(review_cases),
            "generator_scripts": sorted(generator_scripts),
            "generator_script_sha256": sorted(generator_hashes),
            "checks": coverage,
        },
        "videos": results,
        "passed": all(coverage.values()) and all(item["passed"] for item in results.values()),
        "visual_review": "Pending the user's single combined review.",
        "promotion": "Candidates remain outside outputs until that review passes.",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(batch, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(batch, ensure_ascii=False, indent=2))
    if not batch["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
