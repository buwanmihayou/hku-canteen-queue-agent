"""Synthetic model checks; these do not establish measured queue accuracy."""

from datetime import datetime, time, timezone
import math
import unittest

from calibration import (
    CAMPUS_LOCATIONS, HK_TIMEZONE, STALL_RATES, TEMPORAL_PROFILES,
    TIME_CURVE_KNOTS, estimate_wait_minutes, estimated_queue_count,
    hong_kong_time, queue_multiplier,
)
from routing import WALK_TIMES, rank_canteens


class TemporalCalibrationTests(unittest.TestCase):
    def test_covers_eight_canteens_and_seven_origins(self):
        self.assertEqual(len(STALL_RATES), 8)
        self.assertEqual(set(STALL_RATES), set(TEMPORAL_PROFILES))
        self.assertEqual(len(CAMPUS_LOCATIONS), 7)
        self.assertEqual(set(CAMPUS_LOCATIONS), set(WALK_TIMES))

    def test_peak_and_off_peak_values(self):
        for name, profile in TEMPORAL_PROFILES.items():
            with self.subTest(canteen=name):
                self.assertAlmostEqual(queue_multiplier(name, time(10)), profile["off_peak_weight"])
                self.assertAlmostEqual(queue_multiplier(name, time(12)), profile["lunch_peak_weight"])
                self.assertAlmostEqual(queue_multiplier(name, time(12, 30)), profile["lunch_peak_weight"])
                self.assertAlmostEqual(queue_multiplier(name, time(18)), profile["dinner_peak_weight"])
                self.assertGreater(estimated_queue_count(name, time(12)), estimated_queue_count(name, time(10)))
                self.assertGreater(estimated_queue_count(name, time(18)), estimated_queue_count(name, time(15)))
                self.assertNotEqual(estimated_queue_count(name, time(12)), estimated_queue_count(name, time(18)))

    def test_interpolation_and_continuity_at_every_boundary(self):
        for name in STALL_RATES:
            for minute, _, _ in TIME_CURVE_KNOTS[1:-1]:
                center = queue_multiplier(name, time(minute // 60, minute % 60))
                before_second, after_second = minute * 60 - 1, minute * 60 + 1
                before = queue_multiplier(name, time(before_second // 3600, before_second % 3600 // 60, before_second % 60))
                after = queue_multiplier(name, time(after_second // 3600, after_second % 3600 // 60, after_second % 60))
                with self.subTest(canteen=name, minute=minute):
                    self.assertLess(abs(before - center), 0.01)
                    self.assertLess(abs(after - center), 0.01)
            self.assertAlmostEqual(queue_multiplier(name, time(17, 45)), (queue_multiplier(name, time(17, 30)) + queue_multiplier(name, time(18))) / 2)
            self.assertAlmostEqual(queue_multiplier(name, time(0)), queue_multiplier(name, time(23, 59, 59)))

    def test_timezone_conversion(self):
        name = next(iter(STALL_RATES))
        utc = datetime(2026, 11, 8, 4, tzinfo=timezone.utc)
        hk = datetime(2026, 11, 8, 12, tzinfo=HK_TIMEZONE)
        self.assertEqual(hong_kong_time(utc), time(12))
        self.assertEqual(queue_multiplier(name, utc), queue_multiplier(name, hk))
        self.assertEqual(queue_multiplier(name, utc), queue_multiplier(name, time(12)))
        self.assertEqual(queue_multiplier(name, time(4, tzinfo=timezone.utc)), queue_multiplier(name, time(12)))

    def test_default_uses_current_hk_clock(self):
        before = datetime.now(HK_TIMEZONE)
        result = hong_kong_time()
        after = datetime.now(HK_TIMEZONE)
        self.assertTrue(before.time() <= result <= after.time())

    def test_observed_counts_are_not_double_scaled(self):
        for name, info in STALL_RATES.items():
            self.assertEqual(estimate_wait_minutes(name, people_count=0, dining_time=time(12)), 0)
            for hour in (10, 12, 18):
                self.assertAlmostEqual(estimate_wait_minutes(name, 5, time(hour)), 5 * info["rate_min_per_person"])

    def test_bad_counts_rates_times_and_names(self):
        name = next(iter(STALL_RATES))
        for count in (-1, float("inf"), float("nan"), "8", True):
            with self.subTest(count=count), self.assertRaises(ValueError):
                estimate_wait_minutes(name, people_count=count)
        for rate in (-1, 0, float("nan"), float("inf"), "0.8", True):
            with self.subTest(rate=rate), self.assertRaises(ValueError):
                estimate_wait_minutes(name, rate_min_per_person=rate)
        with self.assertRaises(ValueError):
            queue_multiplier("Unknown", time(12))
        with self.assertRaises(TypeError):
            queue_multiplier(name, "12:00")

    def test_synthetic_every_minute_canteen_is_finite(self):
        # 11,520 synthetic canteen/minute evaluations including every boundary.
        for minute in range(1440):
            at = time(minute // 60, minute % 60)
            for name in STALL_RATES:
                count = estimated_queue_count(name, at)
                wait = estimate_wait_minutes(name, dining_time=at)
                self.assertTrue(math.isfinite(count) and count >= 0)
                self.assertTrue(math.isfinite(wait) and wait >= 0)

    def test_synthetic_routing_load_across_origins_urgency_windows(self):
        # 19 times x 7 origins x 2 urgency modes x 8 canteens = 2,128 records.
        samples = (
            time(0), time(10), time(11, 29), time(11, 30), time(11, 50),
            time(12), time(12, 30), time(12, 50), time(13, 30), time(14, 30),
            time(17), time(17, 29), time(17, 30), time(18), time(18, 30),
            time(19), time(19, 30), time(21), time(23, 59),
        )
        for at in samples:
            for origin in CAMPUS_LOCATIONS:
                for rush in (False, True):
                    with self.subTest(at=at, origin=origin, rush=rush):
                        ranked = rank_canteens(STALL_RATES, origin, rush, dining_time=at)
                        self.assertEqual(len(ranked), 8)
                        self.assertEqual([row[4] for row in ranked], sorted(row[4] for row in ranked))
                        for name, walk, wait, total, score in ranked:
                            self.assertEqual(walk, WALK_TIMES[origin][name])
                            self.assertAlmostEqual(wait, estimate_wait_minutes(name, dining_time=at))
                            self.assertAlmostEqual(total, walk + wait)
                            self.assertAlmostEqual(score, walk * (1.5 if rush else 1) + wait)

    def test_partial_manual_counts_and_unknown_canteens(self):
        name = next(iter(STALL_RATES))
        ranked = rank_canteens(STALL_RATES, "Main Building", dining_time=time(12), queue_counts={name: 0})
        self.assertEqual(next(row[2] for row in ranked if row[0] == name), 0)
        self.assertTrue(all(row[2] > 0 for row in ranked if row[0] != name))
        with self.assertRaises(ValueError):
            rank_canteens(STALL_RATES, "Main Building", queue_counts={"Unknown": 5})
        with self.assertRaises(ValueError):
            rank_canteens({"Unknown": {"rate_min_per_person": 1}}, "Main Building")


if __name__ == "__main__":
    unittest.main()
