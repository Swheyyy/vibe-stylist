import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from color_engine.analyzer import build_color_profile
from color_engine.extractor import extract_skin_lab


def load_manifest(manifest_path: Path) -> dict[str, Any]:
    with manifest_path.open("r", encoding="utf-8") as infile:
        manifest = json.load(infile)

    if "samples" not in manifest or not isinstance(manifest["samples"], list):
        raise ValueError("Manifest must include a 'samples' list.")
    return manifest


def safe_lower(value: Any) -> str | None:
    if value is None:
        return None
    return str(value).strip().lower()


def evaluate_manifest(manifest: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    samples = manifest["samples"]
    undertone_hits = 0
    undertone_total = 0
    contrast_hits = 0
    contrast_total = 0
    l_errors: list[float] = []
    failures: list[dict[str, str]] = []
    per_sample: list[dict[str, Any]] = []

    for sample in samples:
        sample_id = sample.get("id", "unknown")
        image_path = sample.get("image_path")
        labels = sample.get("labels", {})

        if not image_path:
            failures.append({"id": sample_id, "error": "Missing image_path"})
            continue

        absolute_image_path = repo_root / image_path
        if not absolute_image_path.exists():
            failures.append(
                {
                    "id": sample_id,
                    "error": f"Image not found: {absolute_image_path}",
                }
            )
            continue

        try:
            lab = extract_skin_lab(str(absolute_image_path))
            profile = build_color_profile(lab)
        except Exception as exc:
            failures.append({"id": sample_id, "error": str(exc)})
            continue

        gt_undertone = safe_lower(labels.get("undertone"))
        gt_contrast = safe_lower(labels.get("contrast"))
        pred_undertone = safe_lower(profile.get("undertone"))
        pred_contrast = safe_lower(profile.get("contrast"))

        undertone_match = None
        contrast_match = None

        if gt_undertone:
            undertone_total += 1
            undertone_match = gt_undertone == pred_undertone
            if undertone_match:
                undertone_hits += 1

        if gt_contrast:
            contrast_total += 1
            contrast_match = gt_contrast == pred_contrast
            if contrast_match:
                contrast_hits += 1

        gt_skin_l = labels.get("skin_L")
        if gt_skin_l is not None:
            try:
                l_errors.append(abs(float(gt_skin_l) - float(profile.get("skin_L", 0.0))))
            except (TypeError, ValueError):
                failures.append(
                    {
                        "id": sample_id,
                        "error": "Invalid labels.skin_L; must be numeric",
                    }
                )

        per_sample.append(
            {
                "id": sample_id,
                "image_path": image_path,
                "ground_truth": {
                    "undertone": gt_undertone,
                    "contrast": gt_contrast,
                    "skin_L": gt_skin_l,
                },
                "prediction": profile,
                "matches": {
                    "undertone": undertone_match,
                    "contrast": contrast_match,
                },
            }
        )

    return {
        "dataset_name": manifest.get("dataset_name", "unknown"),
        "dataset_version": manifest.get("version", "unknown"),
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "num_samples": len(samples),
        "processed_samples": len(per_sample),
        "failures": failures,
        "metrics": {
            "undertone_accuracy": (
                undertone_hits / undertone_total if undertone_total > 0 else None
            ),
            "contrast_accuracy": (
                contrast_hits / contrast_total if contrast_total > 0 else None
            ),
            "skin_l_mae": (mean(l_errors) if l_errors else None),
        },
        "counts": {
            "undertone_labeled": undertone_total,
            "contrast_labeled": contrast_total,
            "skin_l_labeled": len(l_errors),
        },
        "samples": per_sample,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run baseline color-analysis evaluation.")
    parser.add_argument(
        "--manifest",
        required=True,
        help="Path to evaluation manifest JSON (relative to repo root or absolute).",
    )
    parser.add_argument(
        "--output",
        default="evaluation/reports/baseline_latest.json",
        help="Path to write evaluation JSON report.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = repo_root / manifest_path

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = repo_root / output_path

    manifest = load_manifest(manifest_path)
    report = evaluate_manifest(manifest, repo_root=repo_root)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as outfile:
        json.dump(report, outfile, indent=2)

    print(f"Baseline report saved: {output_path}")
    print(f"Processed: {report['processed_samples']} / {report['num_samples']}")
    print(f"Failures: {len(report['failures'])}")
    print(f"Undertone accuracy: {report['metrics']['undertone_accuracy']}")
    print(f"Contrast accuracy: {report['metrics']['contrast_accuracy']}")
    print(f"Skin L MAE: {report['metrics']['skin_l_mae']}")


if __name__ == "__main__":
    main()
