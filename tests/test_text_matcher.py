from utils.data.text_matcher import find_closest


class TestFuzzyMatcher:
    def test_exact_match(self):
        choices = ["Gaming Slippers", "Waterproof Hiking Boots", "Shiroko"]
        assert (
            find_closest("Waterproof Hiking Boots", choices)
            == "Waterproof Hiking Boots"
        )

    def test_typo_correction(self):
        choices = ["Leather Boots", "Skill Book"]
        # rapidfuzz handles common OCR typos
        assert find_closest("Leahter Boots", choices, threshold=0.75) == "Leather Boots"
        assert find_closest("Skil Bok", choices, threshold=0.7) == "Skill Book"

    def test_no_match_below_threshold(self):
        choices = ["Leather Boots"]
        assert find_closest("CompletelyRandom", choices, threshold=0.9) is None

    def test_empty_inputs(self):
        assert find_closest("", ["A", "B"]) is None
        assert find_closest("A", []) is None
        assert find_closest("", []) is None

    def test_threshold_control(self):
        choices = [
            "Shiroko",
            "Shiroko (Swimsuit)",
            "Shiroko (Cycling)",
            "Shiroko*Terror",
        ]

        # Low threshold: matches despite typo
        assert find_closest("Shirokko", choices, threshold=0.6) is not None
        # High threshold: no match
        assert find_closest("Shirokko", choices, threshold=0.95) is None
        # Find Kuroko
        assert find_closest("Shiroko Terror", choices, threshold=0.95) is None
