from __future__ import annotations

import cv2
import numpy as np


def _load_image(image_path: str) -> np.ndarray:
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not read image: {image_path}")
    return image


def _get_face_detector() -> cv2.CascadeClassifier:
    detector_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(detector_path)
    if detector.empty():
        raise RuntimeError("Failed to load OpenCV face detector.")
    return detector


def _largest_face_box(faces: np.ndarray) -> tuple[int, int, int, int]:
    x, y, w, h = max(faces, key=lambda face: face[2] * face[3])
    return int(x), int(y), int(w), int(h)


def _safe_center_crop(image: np.ndarray) -> np.ndarray:
    h, w, _ = image.shape
    y1, y2 = h // 4, (3 * h) // 4
    x1, x2 = w // 4, (3 * w) // 4
    crop = image[y1:y2, x1:x2]
    if crop.size == 0:
        raise ValueError("Image is too small for center crop fallback.")
    return crop


def _face_roi(image: np.ndarray, detector: cv2.CascadeClassifier) -> tuple[np.ndarray, bool]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = detector.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(80, 80),
    )
    if len(faces) == 0:
        return _safe_center_crop(image), False

    x, y, w, h = _largest_face_box(faces)

    # Reduce hair/background influence by using a central-lower facial band.
    fx1 = x + int(0.15 * w)
    fx2 = x + int(0.85 * w)
    fy1 = y + int(0.28 * h)
    fy2 = y + int(0.82 * h)

    fx1 = max(fx1, 0)
    fy1 = max(fy1, 0)
    fx2 = min(fx2, image.shape[1])
    fy2 = min(fy2, image.shape[0])

    face_roi = image[fy1:fy2, fx1:fx2]
    if face_roi.size == 0:
        return _safe_center_crop(image), False
    return face_roi, True


def _skin_mask(roi_bgr: np.ndarray) -> np.ndarray:
    ycrcb = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2YCrCb)

    # Broad skin-range thresholds in YCrCb. Tunable in later research phases.
    lower = np.array([0, 133, 77], dtype=np.uint8)
    upper = np.array([255, 173, 127], dtype=np.uint8)
    mask = cv2.inRange(ycrcb, lower, upper)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
    return mask


def _lab_stats_from_mask(roi_bgr: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, int]:
    lab = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2LAB)
    pixels = lab[mask > 0]
    return pixels, int(pixels.shape[0])


def extract_skin_lab(image_path: str) -> dict[str, float | int | bool | list[str] | str]:
    image = _load_image(image_path)
    detector = _get_face_detector()
    roi_bgr, face_detected = _face_roi(image, detector)

    mask = _skin_mask(roi_bgr)
    pixels, pixel_count = _lab_stats_from_mask(roi_bgr, mask)

    quality_flags: list[str] = []
    method = "face_skin_mask" if face_detected else "center_crop_fallback"

    if pixel_count < 250:
        quality_flags.append("low_skin_pixel_count")
        roi_lab = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2LAB)
        pixels = roi_lab.reshape(-1, 3)
        pixel_count = int(pixels.shape[0])
        method = f"{method}_no_mask_fallback"

    if pixel_count == 0:
        raise ValueError("No valid pixels found for skin LAB extraction.")

    l_values = pixels[:, 0].astype(np.float32)
    a_values = pixels[:, 1].astype(np.float32)
    b_values = pixels[:, 2].astype(np.float32)

    return {
        "L": float(np.mean(l_values)),
        "A": float(np.mean(a_values)),
        "B": float(np.mean(b_values)),
        "L_std": float(np.std(l_values)),
        "pixel_count": pixel_count,
        "face_detected": face_detected,
        "method": method,
        "quality_flags": quality_flags,
    }
