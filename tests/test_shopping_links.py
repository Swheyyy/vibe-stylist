import unittest

from color_engine.shopping_links import generate_shopping_links


class ShoppingLinksTests(unittest.TestCase):
    def test_generate_shopping_links_structure(self):
        profile = {"undertone": "warm"}
        context = {
            "gender": "male",
            "budget_tier": "low",
            "campus_style": "streetwear",
            "occasion": "class day",
            "season": "summer",
        }
        payload = generate_shopping_links(profile, context)

        self.assertIn("categories", payload)
        self.assertIn("tops", payload["categories"])
        self.assertGreater(len(payload["categories"]["tops"]), 0)
        sample = payload["categories"]["tops"][0]
        self.assertIn("retailer", sample)
        self.assertIn("url", sample)


if __name__ == "__main__":
    unittest.main()
