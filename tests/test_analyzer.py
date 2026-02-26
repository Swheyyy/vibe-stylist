import unittest

from color_engine.analyzer import build_color_profile, detect_contrast, detect_undertone


class AnalyzerTests(unittest.TestCase):
    def test_detect_undertone_warm(self):
        undertone, confidence, score = detect_undertone(130.0, 150.0)
        self.assertEqual(undertone, "warm")
        self.assertGreater(confidence, 0.0)
        self.assertGreater(score, 0.0)

    def test_detect_undertone_neutral(self):
        undertone, _, _ = detect_undertone(132.0, 134.0)
        self.assertEqual(undertone, "neutral")

    def test_detect_contrast_low(self):
        contrast, confidence = detect_contrast(150.0, 7.0)
        self.assertEqual(contrast, "low")
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)

    def test_build_color_profile_schema(self):
        profile = build_color_profile(
            {
                "L": 165.0,
                "A": 136.0,
                "B": 149.0,
                "L_std": 12.5,
                "pixel_count": 1800,
                "face_detected": True,
                "method": "face_skin_mask",
                "quality_flags": [],
            }
        )
        self.assertIn("undertone", profile)
        self.assertIn("contrast", profile)
        self.assertIn("confidence", profile)
        self.assertIn("skin_lab", profile)
        self.assertIn("diagnostics", profile)
        self.assertEqual(profile["diagnostics"]["pixel_count"], 1800)


if __name__ == "__main__":
    unittest.main()
