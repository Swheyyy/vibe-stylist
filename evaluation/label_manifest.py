import argparse
import json
from pathlib import Path
from typing import Any

UNDERTONE_CHOICES = {
    "w": "warm",
    "c": "cool",
    "n": "neutral",
}

CONTRAST_CHOICES = {
    "h": "high",
    "m": "medium",
    "l": "low",
}


def load_manifest(manifest_path: Path) -> dict[str, Any]:
    with manifest_path.open("r", encoding="utf-8") as infile:
        manifest = json.load(infile)
    if "samples" not in manifest or not isinstance(manifest["samples"], list):
        raise ValueError("Manifest must contain a 'samples' list.")
    return manifest


def write_manifest(manifest: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as outfile:
        json.dump(manifest, outfile, indent=2)


def ask_choice(prompt: str, choices: dict[str, str], allow_skip: bool = True) -> str | None:
    options = ", ".join([f"{key}={value}" for key, value in choices.items()])
    suffix = ", s=skip, q=quit" if allow_skip else ", q=quit"

    while True:
        raw = input(f"{prompt} ({options}{suffix}): ").strip().lower()
        if raw == "q":
            raise KeyboardInterrupt("Labeling stopped by user.")
        if allow_skip and raw == "s":
            return None
        if raw in choices:
            return choices[raw]
        print("Invalid choice. Try again.")


def ask_skin_l(current_value: Any) -> float | None:
    while True:
        raw = input(
            f"skin_L [0-255] (Enter=keep current '{current_value}', s=clear, q=quit): "
        ).strip().lower()
        if raw == "q":
            raise KeyboardInterrupt("Labeling stopped by user.")
        if raw == "":
            try:
                if current_value is None:
                    return None
                return float(current_value)
            except (TypeError, ValueError):
                return None
        if raw == "s":
            return None
        try:
            value = float(raw)
        except ValueError:
            print("Invalid number. Try again.")
            continue
        if value < 0 or value > 255:
            print("skin_L must be in 0 to 255 for current baseline.")
            continue
        return value


def is_labeled(sample: dict[str, Any]) -> bool:
    labels = sample.get("labels", {})
    return bool(labels.get("undertone")) and bool(labels.get("contrast"))


def run_labeling(manifest: dict[str, Any], output_path: Path, relabel: bool) -> None:
    samples = manifest["samples"]
    labeled_count = 0
    skipped_count = 0

    for sample in samples:
        sample_id = sample.get("id", "unknown")
        image_path = sample.get("image_path", "unknown")
        labels = sample.setdefault("labels", {})

        if is_labeled(sample) and not relabel:
            skipped_count += 1
            continue

        print("\n---")
        print(f"id: {sample_id}")
        print(f"image_path: {image_path}")
        print(f"current labels: {labels}")

        undertone = ask_choice("undertone", UNDERTONE_CHOICES)
        if undertone is None:
            skipped_count += 1
            continue

        contrast = ask_choice("contrast", CONTRAST_CHOICES)
        if contrast is None:
            skipped_count += 1
            continue

        skin_l = ask_skin_l(labels.get("skin_L"))

        labels["undertone"] = undertone
        labels["contrast"] = contrast
        labels["skin_L"] = skin_l
        labeled_count += 1

        # Save after each sample so progress is never lost.
        write_manifest(manifest, output_path)
        print("Saved.")

    write_manifest(manifest, output_path)
    print("\nLabeling complete.")
    print(f"Newly labeled samples: {labeled_count}")
    print(f"Skipped samples: {skipped_count}")
    print(f"Output: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Interactive labeling for manifest samples.")
    parser.add_argument(
        "--manifest",
        default="evaluation/datasets/manifest.to_label.json",
        help="Input manifest path.",
    )
    parser.add_argument(
        "--output",
        default="evaluation/datasets/manifest.json",
        help="Output manifest path (autosaved during labeling).",
    )
    parser.add_argument(
        "--relabel",
        action="store_true",
        help="Relabel samples that already have undertone and contrast values.",
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

    try:
        run_labeling(manifest=manifest, output_path=output_path, relabel=args.relabel)
    except KeyboardInterrupt:
        write_manifest(manifest, output_path)
        print(f"\nStopped early. Progress saved to: {output_path}")


if __name__ == "__main__":
    main()
