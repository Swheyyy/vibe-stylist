import unittest
from unittest.mock import patch

from color_engine.groq_generator import generate_palettes


class GroqGeneratorTests(unittest.TestCase):
    def test_generate_palettes_uses_fallback_on_failure(self):
        profile = {"undertone": "warm", "contrast": "medium", "skin_L": 150.0}

        with patch("color_engine.groq_generator._groq_client", side_effect=RuntimeError("no key")):
            payload = generate_palettes(profile, context={"mood": "bold"})

        self.assertIn("summary", payload)
        self.assertIn("palettes", payload)
        self.assertEqual(len(payload["palettes"]), 3)
        self.assertIn("Fallback", payload["summary"])


if __name__ == "__main__":
    unittest.main()
