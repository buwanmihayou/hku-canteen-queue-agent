"""Validate real queue-photo labels and evaluate frozen model counts without network calls."""
from __future__ import annotations
import argparse
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
from PIL import Image
from routing import WALK_TIMES

FIELDS = ("id", "campus", "canteen", "captured_at", "image_path", "manual_count", "predicted_count")
CANTEEN_CAMPUSES = {name: ("Centennial" if name.startswith(("alfafa", "TamJai", "Asian Gourmet")) else "Main") for name in next(iter(WALK_TIMES.values()))}


def _metrics(samples):
    errors = [abs(row["predicted_count"] - row["manual_count"]) for row in samples]
    total_manual, total_error = sum(row["manual_count"] for row in samples), sum(errors)
    positive = [(row, error) for row, error in zip(samples, errors) if row["manual_count"] > 0]
    return {
        "sample_count": len(samples), "manual_people_total": total_manual, "absolute_error_total": total_error,
        "mae_people": total_error / len(samples) if samples else None,
        "wape": total_error / total_manual if total_manual else (0.0 if samples and total_error == 0 else None),
        "mape_positive_counts": sum(error / row["manual_count"] for row, error in positive) / len(positive) if positive else None,
        "zero_count_samples": sum(row["manual_count"] == 0 for row in samples),
        "zero_count_false_positives": sum(row["manual_count"] == 0 and row["predicted_count"] > 0 for row in samples),
        "exact_matches": sum(error == 0 for error in errors),
    }


def evaluate_manifest(manifest_path, min_samples=25, max_wape=0.10, require_coverage=True):
    """No incomplete rows may enter accuracy metrics; the WAPE gate is strictly <10%."""
    if isinstance(min_samples, bool) or not isinstance(min_samples, int) or min_samples < 1:
        raise ValueError("min_samples must be a positive integer")
    if not 0 < max_wape <= 1:
        raise ValueError("max_wape must be in (0, 1]")
    path = Path(manifest_path).resolve()
    errors, samples = [], []
    report = {"manifest": str(path), "status": "incomplete", "target": {"minimum_photos": min_samples, "wape_strictly_less_than": max_wape, "require_all_canteens_and_campuses": require_coverage}, "errors": errors, "valid_sample_count": 0, "metrics": None, "by_campus": {}, "by_canteen": {}, "samples": samples}
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream, strict=True)
            if reader.fieldnames != list(FIELDS):
                errors.append("CSV header must be exactly: " + ",".join(FIELDS))
                return report
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        errors.append(f"Cannot read manifest: {exc}")
        return report
    ids, hashes = set(), set()
    for number, raw in enumerate(rows, 2):
        prefix = f"Row {number}"
        if None in raw or any(value is None for value in raw.values()):
            errors.append(f"{prefix}: wrong number of CSV cells")
            continue
        row = {key: value.strip() for key, value in raw.items()}
        if not all(row.values()):
            errors.append(f"{prefix}: missing " + ", ".join(field for field in FIELDS if not row[field]))
            continue
        row_errors = []
        if row["id"] in ids:
            row_errors.append("duplicate id")
        ids.add(row["id"])
        expected = CANTEEN_CAMPUSES.get(row["canteen"])
        if expected is None:
            row_errors.append("unknown canteen")
        if row["campus"] not in {"Main", "Centennial"}:
            row_errors.append("campus must be Main or Centennial")
        elif expected is not None and row["campus"] != expected:
            row_errors.append("campus does not match canteen")
        try:
            captured = datetime.fromisoformat(row["captured_at"])
            if captured.tzinfo is None or captured.utcoffset() is None:
                raise ValueError("missing timezone")
        except ValueError:
            row_errors.append("captured_at must be an ISO 8601 datetime with timezone")
        counts = {}
        for field in ("manual_count", "predicted_count"):
            try:
                value = row[field]
                if not value or not value.isascii() or not value.isdigit():
                    raise ValueError()
                counts[field] = int(value)
            except ValueError:
                row_errors.append(f"{field} must be a nonnegative integer")
        image_path = Path(row["image_path"])
        if not image_path.is_absolute():
            image_path = path.parent / image_path
        try:
            data = image_path.read_bytes()
            with Image.open(image_path) as image:
                if image.format not in {"JPEG", "PNG"}:
                    raise ValueError("only actual JPEG or PNG images are supported")
                image.verify()
            with Image.open(image_path) as image:
                image.load()
            digest = hashlib.sha256(data).hexdigest()
            if digest in hashes:
                row_errors.append("duplicate image content")
            hashes.add(digest)
        except (OSError, ValueError, Image.DecompressionBombError) as exc:
            row_errors.append(f"image cannot be decoded: {exc}")
        if row_errors:
            errors.append(f"{prefix} ({row['id']}): " + "; ".join(row_errors))
            continue
        absolute_error = abs(counts["predicted_count"] - counts["manual_count"])
        samples.append({"id": row["id"], "campus": row["campus"], "canteen": row["canteen"], **counts, "absolute_error": absolute_error, "relative_error": absolute_error / counts["manual_count"] if counts["manual_count"] else None})
    report["row_count"], report["valid_sample_count"] = len(rows), len(samples)
    if len(samples) < min_samples:
        errors.append(f"Need at least {min_samples} valid, distinct photos; found {len(samples)}")
    if require_coverage:
        missing = set(CANTEEN_CAMPUSES) - {row["canteen"] for row in samples}
        campuses = {"Main", "Centennial"} - {row["campus"] for row in samples}
        if missing:
            errors.append("Missing canteens: " + "; ".join(sorted(missing)))
        if campuses:
            errors.append("Missing campuses: " + ", ".join(sorted(campuses)))
    if errors:
        return report
    report["metrics"] = _metrics(samples)
    for field in ("campus", "canteen"):
        report[f"by_{field}"] = {group: _metrics([row for row in samples if row[field] == group]) for group in sorted({row[field] for row in samples})}
    wape = report["metrics"]["wape"]
    report["status"] = "passed" if report["metrics"]["manual_people_total"] > 0 and wape is not None and wape < max_wape else "target_missed"
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--min-samples", type=int, default=25)
    parser.add_argument("--max-wape", type=float, default=0.10)
    args = parser.parse_args()
    try:
        report = evaluate_manifest(args.manifest, args.min_samples, args.max_wape)
    except ValueError as exc:
        parser.error(str(exc))
    output = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)
    if args.report:
        if args.report.resolve() == args.manifest.resolve():
            parser.error("Report must not overwrite the manifest")
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output + "\n", encoding="utf-8")
    print(output)
    return {"passed": 0, "target_missed": 1, "incomplete": 2}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
