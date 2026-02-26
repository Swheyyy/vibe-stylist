# Dataset Sourcing Guide (Phase A)

Use a mix of public datasets and your own consented captures.

## Recommended sources

1. Local consented photos
- Best for product realism (your camera conditions, your target users).
- Require explicit user consent and retention policy.

2. Public face datasets (research/legal review required)
- **FFHQ** (high-quality faces, broad variety)
- **UTKFace** (age/gender/ethnicity metadata)
- **CelebA** (large face image set)

3. Controlled studio captures
- Small but high-quality set with known lighting and white-balance cards.
- Ideal for calibration and threshold tuning.

## Minimum starting target

- 150 to 300 images
- Balanced across visible skin tones
- Mixed lighting: daylight, indoor warm, indoor cool
- At least 3 camera types (phone/front/rear/webcam)

## Labeling protocol for Phase A

For each sample:

- `undertone`: warm / cool / neutral (use 2 raters + tie-break process)
- `contrast`: high / medium / low
- `skin_L`: optional reference value in **OpenCV LAB L scale (0 to 255)** for current baseline

## Ethics and legal checks

- Do not scrape copyrighted or private photos without rights.
- Store signed consent for local/user-submitted datasets.
- Add a deletion workflow for user images.
- Keep dataset and model artifacts separate from production uploads.
