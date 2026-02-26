import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def discover_images(images_root: Path) -> list[Path]:
    image_paths: list[Path] = []
    for path in sorted(images_root.rglob("*")):
        if path.is_file() and path.suffix.lower() in ALLOWED_IMAGE_EXTENSIONS:
            image_paths.append(path)
    return image_paths


def build_manifest(images: list[Path], repo_root: Path, dataset_name: str, version: str) -> dict:
    samples = []
    for index, image_path in enumerate(images, start=1):
        relative_path = image_path.relative_to(repo_root).as_posix()
        samples.append(
            {
                "id": f"sample_{index:04d}",
                "image_path": relative_path,
                "labels": {
                    "undertone": None,
                    "contrast": None,
                    "skin_L": None,
                },
            }
        )

    return {
        "dataset_name": dataset_name,
        "version": version,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "notes": "Fill labels with evaluation/label_manifest.py",
        "samples": samples,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an unlabeled manifest from image files.")
    parser.add_argument(
        "--images-root",
        default="evaluation/datasets/local_faces",
        help="Directory containing images (recursive).",
    )
    parser.add_argument(
        "--output",
        default="evaluation/datasets/manifest.to_label.json",
        help="Output manifest JSON path.",
    )
    parser.add_argument("--dataset-name", default="vibe_stylist_local_baseline")
    parser.add_argument("--version", default="1.0.0")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite output file if it already exists.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    images_root = Path(args.images_root)
    if not images_root.is_absolute():
        images_root = repo_root / images_root

    if not images_root.exists():
        raise FileNotFoundError(f"Images root does not exist: {images_root}")

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = repo_root / output_path

    if output_path.exists() and not args.overwrite:
        raise FileExistsError(
            f"Output file already exists: {output_path}. Use --overwrite to replace it."
        )

    images = discover_images(images_root)
    manifest = build_manifest(
        images=images,
        repo_root=repo_root,
        dataset_name=args.dataset_name,
        version=args.version,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as outfile:
        json.dump(manifest, outfile, indent=2)

    print(f"Manifest created: {output_path}")
    print(f"Discovered images: {len(images)}")


if __name__ == "__main__":
    main()
