import unittest

from routing import WALK_TIMES, rank_canteens


STALL_RATES = {
    "CYM Canteen (Chong Yuet Ming Cultural Centre)": {"rate_min_per_person": 0.6},
    "JuYing Tai (Fong Shu Chuen Amenities Centre, Swire Building)": {"rate_min_per_person": 0.6},
    "Union Restaurant (Haking Wong Building)": {"rate_min_per_person": 0.6},
    "alfafa bistro (Jockey Club Tower, Centennial Campus)": {"rate_min_per_person": 1.0},
    "TAI TAI FOODTOPIA (Shop G. 02, G/F, Composite Building, Main Campus)": {"rate_min_per_person": 1.0},
    "TamJai SamGor (G/F The Jockey Club Tower, Centennial Campus)": {"rate_min_per_person": 1.0},
    "Asian Gourmet (G/F, Run Run Shaw Tower, Centennial Campus)": {"rate_min_per_person": 1.5},
    "OORI HANSIK (Shop G. 01, G/F, Composite Building, Main Campus)": {"rate_min_per_person": 2.0},
}


class RoutingTests(unittest.TestCase):
    def test_every_location_has_all_canteens(self):
        expected = set(STALL_RATES)
        for location, walk_times in WALK_TIMES.items():
            self.assertEqual(set(walk_times), expected, location)

    def test_selected_location_changes_recommendation(self):
        cym_results = rank_canteens(STALL_RATES, "Chong Yuet Ming Cultural Centre")
        centennial_results = rank_canteens(STALL_RATES, "Centennial Campus (Grand Hall)")

        cym_order = [result[0] for result in cym_results]
        centennial_order = [result[0] for result in centennial_results]
        self.assertNotEqual(cym_order, centennial_order)
        self.assertNotEqual(cym_results[0][1], centennial_results[0][1])

    def test_total_is_walk_plus_wait(self):
        for _, walk, wait, total, _ in rank_canteens(STALL_RATES, "Main Building"):
            self.assertAlmostEqual(total, walk + wait)

    def test_unknown_location_is_rejected(self):
        with self.assertRaises(ValueError):
            rank_canteens(STALL_RATES, "Unknown Building")


if __name__ == "__main__":
    unittest.main()
