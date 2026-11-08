# Verification results

Verified on Windows on 2026-11-08 using Python 3.12.14, Streamlit 1.67.0,
OpenAI SDK 3.46.0 and Pillow 13.0.0.

- unittest discover: 51 passed, no skipped tests in this environment.
- ty check app.py routing.py calibration.py queue_analysis.py benchmark.py build_offline.py: passed.
- Streamlit real-runtime agent API: initial load and noon route request both ready;
  route request returned 3 recommendations. Server console had no new warnings
  or tracebacks. AppTest emits the documented bare-mode ScriptRunContext warning.
- Installed Google Chrome 157.0.8103.39, headless via Playwright:
  planner and manual wait at widths 320, 375, 390, 768, 1280; no horizontal
  overflow, stException elements or page JavaScript errors.
- Mobile header spacing verified after correction so the fixed toolbar does
  not cover the title.
- PWA at 390 × 844: service worker ready, 3 routes, manual 12-person CYM wait
  9.6 minutes, offline reload works.
- Saved standalone HTML at 320px: opened with networking disabled before load;
  3 routes and zero-person wait calculation work.
- Synthetic calibration checks cover every minute of the day for all 8
  canteens, and route parity checks cover 154 scenarios.

Not verified: physical iOS Safari, physical Android Chrome, WebKit, live
Bailian model connectivity or prediction accuracy on real photos. No real
benchmark dataset was provided; report.json has 0 valid samples and null metrics.
