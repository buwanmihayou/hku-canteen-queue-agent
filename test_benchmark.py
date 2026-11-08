"""Synthetic unit fixtures verify evaluation logic, never real model accuracy."""

import csv
from pathlib import Path
import tempfile
import unittest

from PIL import Image

from benchmark import CANTEEN_CAMPUSES, FIELDS, evaluate_manifest


class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = self.root / "manifest.csv"
        canteens = list(CANTEEN_CAMPUSES)
        self.rows = []
        for index in range(25):
            name = canteens[index % len(canteens)]
            image_path = self.root / f"test_{index}.png"
            Image.new("RGB", (3, 3), (index, 0, 0)).save(image_path)
            self.rows.append({
                "id": f"test_{index}", "campus": CANTEEN_CAMPUSES[name], "canteen": name,
                "captured_at": "2026-11-08T12:00:00+08:00", "image_path": image_path.name,
                "manual_count": "10", "predicted_count": "10",
            })

    def evaluate(self):
        with self.manifest.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(self.rows)
        return evaluate_manifest(self.manifest)

    def test_complete_corpus_has_full_coverage_and_aggregate_metrics(self):
        report = self.evaluate()
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["valid_sample_count"], 25)
        self.assertEqual(report["metrics"]["wape"], 0)
        self.assertEqual(len(report["by_canteen"]), 8)
        self.assertEqual(set(report["by_campus"]), {"Main", "Centennial"})
        self.assertEqual(sum(group["sample_count"] for group in report["by_canteen"].values()), 25)

    def test_exactly_ten_percent_does_not_pass(self):
        for row in self.rows:
            row["predicted_count"] = "11"
        report = self.evaluate()
        self.assertEqual(report["status"], "target_missed")
        self.assertAlmostEqual(report["metrics"]["wape"], 0.10)
        self.assertEqual(report["metrics"]["mae_people"], 1)

    def test_zero_count_false_positive_remains_in_wape(self):
        self.rows[0]["manual_count"] = "0"
        self.rows[0]["predicted_count"] = "2"
        report = self.evaluate()
        self.assertEqual(report["status"], "passed")
        self.assertAlmostEqual(report["metrics"]["wape"], 2 / 240)
        self.assertEqual(report["metrics"]["zero_count_false_positives"], 1)
        self.assertEqual(report["metrics"]["mape_positive_counts"], 0)
        self.assertIsNone(report["samples"][0]["relative_error"])

    def test_all_empty_queues_cannot_pass_accuracy_gate(self):
        for row in self.rows:
            row["manual_count"] = row["predicted_count"] = "0"
        report = self.evaluate()
        self.assertEqual(report["status"], "target_missed")
        self.assertEqual(report["metrics"]["wape"], 0)
        self.assertIsNone(report["metrics"]["mape_positive_counts"])
        self.rows[0]["predicted_count"] = "1"
        report = self.evaluate()
        self.assertIsNone(report["metrics"]["wape"])

    def test_missing_annotation_blocks_partial_metrics(self):
        self.rows[0]["manual_count"] = ""
        report = self.evaluate()
        self.assertEqual(report["status"], "incomplete")
        self.assertIsNone(report["metrics"])
        self.assertIn("missing manual_count", report["errors"][0])

    def test_duplicate_image_content_is_not_an_additional_sample(self):
        self.rows[1]["image_path"] = self.rows[0]["image_path"]
        report = self.evaluate()
        self.assertEqual(report["status"], "incomplete")
        self.assertTrue(any("duplicate image content" in error for error in report["errors"]))

    def test_invalid_or_absent_photo_blocks_evaluation(self):
        for value in ("missing.png", "corrupt.png"):
            with self.subTest(value=value):
                self.rows[0]["image_path"] = value
                (self.root / "corrupt.png").write_text("not an image", encoding="utf-8")
                report = self.evaluate()
                self.assertEqual(report["status"], "incomplete")
                self.assertIsNone(report["metrics"])

    def test_invalid_counts_and_timestamp_are_reported(self):
        self.rows[0]["manual_count"] = "-1"
        self.rows[0]["predicted_count"] = "1.5"
        self.rows[0]["captured_at"] = "2026-11-08T12:00:00"
        report = self.evaluate()
        self.assertEqual(report["status"], "incomplete")
        self.assertIn("manual_count", report["errors"][0])
        self.assertIn("predicted_count", report["errors"][0])
        self.assertIn("timezone", report["errors"][0])

    def test_unknown_canteen_and_campus_mismatch(self):
        self.rows[0]["campus"] = "Centennial"
        self.rows[1]["canteen"] = "Unknown"
        report = self.evaluate()
        self.assertEqual(report["status"], "incomplete")
        self.assertTrue(any("campus does not match" in error for error in report["errors"]))
        self.assertTrue(any("unknown canteen" in error for error in report["errors"]))

    def test_missing_coverage_and_insufficient_sample_size(self):
        self.rows = self.rows[:1]
        report = self.evaluate()
        self.assertEqual(report["status"], "incomplete")
        self.assertTrue(any("at least 25" in error for error in report["errors"]))
        self.assertTrue(any("Missing canteens" in error for error in report["errors"]))
        self.assertTrue(any("Missing campuses" in error for error in report["errors"]))

    def test_duplicate_ids_are_rejected(self):
        self.rows[1]["id"] = self.rows[0]["id"]
        self.assertTrue(any("duplicate id" in error for error in self.evaluate()["errors"]))

    def test_schema_is_strict_and_missing_file_is_incomplete(self):
        self.assertEqual(evaluate_manifest(self.manifest)["status"], "incomplete")
        self.manifest.write_text("id,manual_count\nq1,2\n", encoding="utf-8")
        report = evaluate_manifest(self.manifest)
        self.assertEqual(report["status"], "incomplete")
        self.assertIn("CSV header", report["errors"][0])

    def test_manifest_template_is_explicitly_incomplete(self):
        path = Path(__file__).parent / "benchmarks" / "manifest.csv"
        report = evaluate_manifest(path)
        self.assertEqual(report["row_count"], 25)
        self.assertEqual(report["valid_sample_count"], 0)
        self.assertIsNone(report["metrics"])
        self.assertEqual(report["status"], "incomplete")

    def test_invalid_evaluation_configuration_rejected(self):
        for minimum in (0, -1, 1.5, True):
            with self.subTest(minimum=minimum), self.assertRaises(ValueError):
                evaluate_manifest(self.manifest, min_samples=minimum)
        for threshold in (0, -0.1, 1.1, float("nan")):
            with self.subTest(threshold=threshold), self.assertRaises(ValueError):
                evaluate_manifest(self.manifest, max_wape=threshold)


if __name__ == "__main__":
    unittest.main()
