# HKU Canteen Queue Assistant

Implementation of the three follow-up milestones in Group 37's midterm status sheet.
The planner covers 8 canteens and 7 starting locations. All queue curves, service
rates and walking times remain empirical assumptions awaiting field validation.

## Run

Use Python 3.12 (tested on Windows with Streamlit 1.67.0, OpenAI SDK 3.46.0
and Pillow 13.0.0).

~~~powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python build_offline.py
python -m streamlit run app.py
~~~

The route planner and manual headcount calculator work without an API key.
The optional cloud features use DASHSCOPE_API_KEY and DASHSCOPE_BASE_URL
from environment variables or .streamlit/secrets.toml. The default endpoint
and qwen3.8-flash model are retained from the original course project.
A working instructor-issued key is still required for actual cloud inference.
Never commit secrets.

## Behavior

- Select a Hong Kong dining time to apply continuous lunch and dinner demand
  curves. The Top 3 ranking combines walking time with assumed queue wait.
  Rush mode ranks using 1.5 × walk + wait; displayed totals remain walk + wait.
- Manual count uses count × service rate, without multiplying an observed queue
  by the time-of-day curve again.
- Photo mode requires an upload and explicit consent before sending a resized
  JPEG to Alibaba Cloud. The app writes no photo files; provider retention may
  differ. Empty, damaged, unsupported, oversized and irrelevant inputs have
  controlled outcomes. Cloud failure never generates a fake observed count.
- Synthetic demo uses 16 example people, clearly separated from real inference.
- No CCTV, opening-hours integration, local Ollama model or custom model
  training is implemented.

## Real photo benchmark

benchmarks/manifest.csv contains 25 planned sample rows across both campuses
and all 8 canteens. Real photos and labels are absent. Follow benchmarks/README.md
to collect distinct photos and enter manual and frozen model counts.

~~~powershell
python benchmark.py benchmarks/manifest.csv --report benchmarks/report.json
~~~

Exit 0 means a complete corpus meets aggregate WAPE strictly below 10%;
1 means the accuracy target was missed; 2 means evidence is incomplete.
WAPE is sum of absolute errors divided by total manual headcount.
MAE, positive-count MAPE, per-photo errors and campus/canteen groups are also
reported. An all-empty corpus cannot pass the accuracy gate.

## Offline use

Save offline/offline.html or download it from the Streamlit app before losing
the connection. The saved file runs routes and manual counts without a server.
The Streamlit page itself needs its Python server connection.

For the PWA, serve offline/ over HTTPS or localhost and wait for "Offline ready".
See offline/README.md. No external CDN or cloud API is needed. Rebuild after
changing calibration.py or routing.py.

## Verify

~~~powershell
python -m unittest discover -v
~~~

51 tests passed. If Node.js is absent, the JavaScript/Python parity test is
skipped; install Node.js to run it. Tests use synthetic inputs and mocked cloud
responses, not real headcount accuracy measurements. Chrome headless checks
covered widths 320, 375, 390, 768 and 1280 and offline reload. Physical mobile
Safari and Chrome remain unverified.

CALIBRATION_NOTES.md describes the curve assumptions. TEST_RESULTS.md records
the verified scope. Real photo collection and physical phone validation remain pending.
