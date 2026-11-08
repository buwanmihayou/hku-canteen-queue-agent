# Queue photo benchmark

The midterm sheet calls for 25 real queue photos from Main and Centennial campuses, manual headcounts, and estimation error below 10%. This folder supplies the collection plan and evaluator. No real photos have been collected here and model accuracy has not been established. Empty evidence cells in manifest.csv are intentional.

## Collect and annotate

1. Collect at least 25 distinct permitted queue photographs covering all eight canteens and both campuses. The prefilled campus and canteen columns in manifest.csv are a sampling plan, not evidence of visits. Include lunch, dinner, quiet periods, different viewpoints, short/long queues and empty queues.
2. Avoid identifiable faces, receipts and screens. Keep real images private and do not commit them. The images directory is Git-ignored. Use de-identified copies where needed and record the actual capture time rather than an example date.
3. Set image_path relative to this manifest, such as images/q001.jpg, or use an absolute local path. Use actual JPEG or PNG files. Duplicate image bytes cannot count as additional photos.
4. Set captured_at to the actual ISO 8601 timestamp with timezone, for example 2026-11-09T12:10:00+08:00. Main and Centennial are the only campus values. Canteen names must exactly match the application.
5. Have two annotators independently count customers visibly waiting in the designated queue, excluding staff, seated diners and passers-by. Resolve disagreements and record manual_count; zero means a verified empty queue. Leave uncertain images out.
6. Freeze the model and prompt before evaluation. Fill predicted_count from an actual image inference run and record model, prompt revision and inference date separately. Do not copy manual_count or use a fixed demonstration, manual fallback or assumed baseline as a model prediction. Leave predictions blank while the API key is unavailable.

The CSV header must be exactly:

```csv
id,campus,canteen,captured_at,image_path,manual_count,predicted_count
```

## Evaluate

From the repository directory after installing requirements:

```powershell
python benchmark.py benchmarks/manifest.csv --report benchmarks/report.json
```

The evaluator makes no network calls. It verifies the full CSV, actual image decoding, unique IDs and image content, valid timestamps, nonnegative integer counts, at least 25 samples, both campuses and all eight canteens. Incomplete evidence produces status incomplete and no aggregate accuracy metrics; it never silently evaluates only successful rows.

| Exit code | Meaning |
| --- | --- |
| 0 | Complete evidence and WAPE strictly below 10% |
| 1 | Complete evidence but target missed, including an all-empty-queue corpus |
| 2 | Incomplete or invalid evidence or command arguments |

## Metrics

- WAPE is sum(abs(predicted_count - manual_count)) / sum(manual_count). Acceptance uses strictly less than 0.10, so exactly 10% fails. This operational definition of the sheet error target should be agreed with the teaching team if another metric is required.
- MAE is mean absolute error in people. Positive-only MAPE averages per-photo relative errors only where manual_count is greater than zero.
- Empty-queue false positives remain in the WAPE numerator; per-photo relative_error is null when manual_count is zero. If all manual counts are zero, WAPE is zero only for exact predictions and otherwise null; neither case passes because the corpus does not demonstrate real queue counting.
- JSON includes per-photo errors and metrics grouped by campus and canteen. The gate evaluates overall WAPE, not a claim that every individual photograph has error below 10%.

The unit tests use tiny generated images only to verify validation and arithmetic. They are not queue photographs or evidence of model accuracy.
