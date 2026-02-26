# Phase A - Baseline Evaluation

This folder contains the first research-layer scaffold for Vibe Stylist:

- A labeled dataset manifest format
- Baseline metrics for the current color analysis logic
- A script to run reproducible evaluation reports
- Dataset sourcing and labeling guidance
- Foundational labeling workflow scripts

## Why this exists

Before changing algorithms, you need baseline numbers so improvements can be measured, not guessed.

For dataset acquisition strategy, see:

`evaluation/dataset_sourcing.md`

## Dataset structure

Keep local evaluation images in:

`evaluation/datasets/local_faces/`

## Labeling workflow (Phase A.1 foundational)

### Step 1: Initialize an unlabeled manifest

```powershell
python -m evaluation.init_manifest --images-root evaluation/datasets/local_faces --output evaluation/datasets/manifest.to_label.json
```

### Step 2: Label samples interactively

```powershell
python -m evaluation.label_manifest --manifest evaluation/datasets/manifest.to_label.json --output evaluation/datasets/manifest.json
```

Label shortcuts:

- Undertone: `w` warm, `c` cool, `n` neutral
- Contrast: `h` high, `m` medium, `l` low
- `s` skips current field or sample, `q` quits and saves progress

### Step 3: Run baseline evaluation

```powershell
python -m evaluation.run_baseline --manifest evaluation/datasets/manifest.json
```

Optional report path:

```powershell
python -m evaluation.run_baseline --manifest evaluation/datasets/manifest.json --output evaluation/reports/latest.json
```

## Alternative quick-start template

If you want manual editing instead of interactive labeling, use:

`evaluation/datasets/manifest.example.json`

Then copy it to:

`evaluation/datasets/manifest.json`

and replace labels with your own annotated ground truth.

## Manifest schema

Each item in `samples` must include:

- `id` (string): sample identifier
- `image_path` (string): path relative to repository root
- `labels.undertone` (string): `warm` / `cool` / `neutral`
- `labels.contrast` (string): `high` / `medium` / `low`
- `labels.skin_L` (number, optional): expected LAB L channel reference

## Output metrics

The baseline script produces:

- `num_samples`
- `processed_samples`
- `failures`
- `undertone_accuracy`
- `contrast_accuracy`
- `skin_l_mae` (mean absolute error, when `labels.skin_L` exists)

It also stores per-sample predictions to support error analysis.
