# HKU Canteen Peak-Hour Queue Assistant

An AI-powered dining and transit optimization system engineered for The University of Hong Kong (HKU) community to alleviate peak-hour dining congestion (11:50-13:30 and 17:30-19:00).

The system integrates a hybrid decision-making architecture: combining empirical path-finding algorithms with Alibaba Cloud Bailian (Qwen3.8-Flash) personalized guidance, zero-shot queue analysis, and deterministic fallback caches, served via a Streamlit web interface.

Live Cloud Demo: https://hku-canteen-agent.streamlit.app
(No local installation or GPU required for peer reviewers and teaching team)

---

## Key Features

1. Dynamic Transit and Congestion Planner (Tab 1)
- Location-Aware Routing: Select your current campus landmark (e.g., Main Building, Chong Yuet Ming, Centennial Campus).
- Transit Cost Optimization: Computes empirical transit time combined with peak-hour baseline service delays.
- AI Dining Agent: Leverages the course-sponsored Alibaba Cloud Bailian (qwen3.8-flash) to generate real-time campus transit advice and dining recommendations.

2. Multi-Tier Queue Estimator (Tab 2)
- Photo Queue Analysis: Evaluates crowd density and predicts queue numbers directly from stall photographs.
- Turnaround Speed Matrices: Converts headcounts into predicted wait times using stall-specific metrics (e.g., 1.2 min/person for bistro setups, 0.6 min/person for high-throughput counters).
- Deterministic Fallback Benchmarks: Provides pre-calibrated baseline caching for zero-GPU, offline, or high-concurrency evaluation scenarios.

3. Privacy and Edge-First Safeguards
- Ephemeral In-Memory Processing: Uploaded images are compressed, analyzed in volatile memory, and discarded immediately without logging facial biometric data.

---

## Architecture and Fallback Pipeline

The project features a multi-tier fallback mechanism to guarantee uninterrupted service during grading and demonstrations:

- Primary Engine: Alibaba Cloud Bailian (qwen3.8-flash via Token Plan)
- Secondary Engine: Local Ollama (LLaVA for zero-shot local vision)
- Tertiary Fallback: Deterministic Empirical Heuristics and Offline Benchmark Cache

---

## Quick Start Guide (Local Execution)

If you wish to clone and run the application locally:

1. Clone the Repository
git clone https://github.com/buwanmihayou/hku-canteen-queue-agent.git
cd hku-canteen-queue-agent

2. Install Dependencies
pip install -r requirements.txt

(Core dependencies: streamlit, openai, pillow)

3. Environment Configuration (Optional)
If calling the sponsored cloud models locally, create a file named .streamlit/secrets.toml:
DASHSCOPE_API_KEY = "your-sponsored-api-key"
DASHSCOPE_BASE_URL = "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"

(If no keys are provided, the system seamlessly operates via the local/offline rule-based pipeline).

4. Launch the Web Application
streamlit run app.py

Open your browser at http://localhost:8501.

---

## Evaluation and Reviewer Instructions (Mid-Term Check)

Teaching assistants and peer reviewers can verify reproducibility through either method:

Option A: 1-Click Evaluation via Deployed Cloud App (Recommended)
1. Open the public web portal: https://hku-canteen-agent.streamlit.app
2. Tab 1 (Transit & Peak Planner): Choose your starting point and click "Find Optimal Dining Route" to verify the path-ranking algorithm and Bailian AI recommendations.
3. Tab 2 (Live Queue Estimator): Upload any test canteen picture (PNG/JPG), check "Use benchmark verification cache (Offline test mode)" (or leave unchecked for dynamic inference), and click "Estimate Queue Delays" to inspect the real-time headcount metrics and queue delay estimation.

Option B: Offline Fallback Verification (Zero External APIs)
1. In Tab 2, check "Use benchmark verification cache (Offline test mode)".
2. Run estimation on any image to confirm deterministic, fully reproducible results without network dependencies.

---

## Project Structure

- app.py: Main application, Bailian LLM orchestration, and UI layout
- requirements.txt: Python runtime dependencies
- README.md: Documentation, architecture guide, and evaluation instructions

---

## License and Course Attribution

Developed for AILT9019: Generative AI and Code Agents (Group 37) at The University of Hong Kong (HKU)[cite: 10]. Provided strictly for academic evaluation and research purposes.
