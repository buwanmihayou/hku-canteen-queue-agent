# 🍲 HKU Canteen Peak-Hour Queue Assistant

An AI-powered dining and transit optimization system engineered for the University of Hong Kong (HKU) community to alleviate peak-hour dining congestion (11:50–13:30 & 17:30–19:00).

The system integrates a hybrid decision-making architecture: combining empirical path-finding algorithms with **Alibaba Cloud Bailian (`qwen3.8-flash`)** personalized guidance, zero-shot multimodal queue analysis, and deterministic fallback caches—served via an intuitive Streamlit interface.

> 🌐 **Live Cloud Demo**: [https://hku-canteen-agent.streamlit.app](https://hku-canteen-agent.streamlit.app)  
> *(No local installation or GPU required for peer reviewers and teaching team)*

---

## 🌟 Key Features

### 1. Dynamic Transit & Congestion Planner (Tab 1)
* **Location-Aware Routing**: Select your current campus landmark (e.g., Main Building, Chong Yuet Ming, Centennial Campus).
* **Transit Cost Optimization**: Computes empirical transit time ($T_{\text{walk}}$) combined with peak-hour baseline service delays ($T_{\text{wait}}$).
* **AI Dining Agent**: Leverages the course-sponsored **Alibaba Cloud Bailian (`qwen3.8-flash`)** to generate real-time campus transit advice and dining recommendations.

### 2. Multi-Tier Queue Estimator (Tab 2)
* **Vision-Language Queue Analysis**: Evaluates crowd density and predicts queue numbers directly from stall photographs.
* **Turnaround Speed Matrices**: Converts headcounts into predicted wait times using stall-specific metrics (e.g., 1.2 min/person for bistro setups, 0.6 min/person for high-throughput counters).
* **Deterministic Fallback Benchmarks**: Provides pre-calibrated baseline caching for zero-GPU, offline, or high-concurrency evaluation scenarios.

### 3. Privacy & Edge-First Safeguards
* **Ephemeral In-Memory Processing**: Uploaded images are compressed, analyzed in volatile memory, and discarded immediately without logging facial biometric data.

---

## 🏗️ Architecture & Model Fallback Pipeline

The project features a **multi-tier fallback mechanism** to guarantee uninterrupted service during grading and demonstrations:

$$\text{User Request} \longrightarrow \begin{cases} \text{Primary:} & \text{Alibaba Cloud Bailian (Qwen3.8-Flash / Token Plan)} \\ \text{Secondary:} & \text{Local Ollama (LLaVA) [Optional Local Mode]} \\ \text{Tertiary:} & \text{Deterministic Empirical Heuristics / Offline Cache} \end{cases}$$

---

## 🚀 Quick Start Guide (Local Execution)

If you wish to clone and run the application locally:

### 1. Clone the Repository
```bash
git clone [https://github.com/buwanmihayou/hku-canteen-queue-agent.git](https://github.com/buwanmihayou/hku-canteen-queue-agent.git)
cd hku-canteen-queue-agent
