# 🍲 HKU Canteen Peak-Hour Queue Assistant

An open-source, reproducible AI assistant engineered for the University of Hong Kong (HKU) community to alleviate peak-hour dining congestion (11:50–13:30 & 17:30–19:00). 

The system implements a human-in-the-loop pipeline combining **position-based dynamic route recommendation** and **zero-shot local Vision-Language Model (VLM) queue analysis**, distributed via an intuitive Streamlit single-page interface.

---

## 🌟 Key Features

1. **Walking-and-Waiting Route Planner (Tab 1)**:
   - Takes user current campus location (e.g., Main Building, Chong Yuet Ming, Centennial Campus).
   - Computes empirical transit time ($T_{\text{walk}}$) and combines it with peak-hour baseline delays ($T_{\text{wait}}$).
   - Dynamically ranks the Top-3 dining options sorted by total anticipated time ($T_{\text{total}} = T_{\text{walk}} + T_{\text{wait}}$).

2. **Zero-Shot VLM Queue Headcount Estimator (Tab 2)**:
   - Evaluates queue density and estimates customer counts directly from user-uploaded stall photos.
   - Eliminates custom CNN training bottlenecks by leveraging local multimodal reasoning via `LLaVA` through Ollama.
   - Converts estimated headcounts to real-time wait times using stall-specific processing speed matrices (e.g., $1.2\text{ min/person}$ for bistro setups, $0.6\text{ min/person}$ for quick-service counters).

3. **Privacy & Peer Review Safeguards**:
   - In-memory inference: uploaded images are processed transiently and discarded immediately without logging facial biometric data.
   - **Offline Mock Fallback Cache**: allows zero-GPU / zero-Ollama peer review testing with a single checkbox toggle.

---

## 📋 System Requirements

- **Operating System**: Windows 10/11, macOS, or Linux
- **Python**: 3.9 - 3.12 (compatible with Python 3.14 via module invocation)
- **Local Inference Engine**: [Ollama](https://ollama.com/) (Required only for live local vision model execution; optional for offline test mode)

---

## 🚀 Quick Start Guide

### 1. Clone or Download Repository

```bash
git clone https://github.com/<YOUR_GITHUB_USERNAME>/hku-canteen-queue-agent.git
cd hku-canteen-queue-agent
```

### 2. Install Python Dependencies

Run the following command in your terminal or command prompt:

```bash
pip install streamlit ollama
```

*(Alternatively, run `pip install -r requirements.txt` if using the requirements file).*

### 3. Launch Local Vision Engine (Optional for Live VLM Mode)

Ensure Ollama is running on your machine, then pull and start the compatible multimodal vision model:

```bash
ollama run llava
```

> **Note**: If you do not have Ollama installed or lack GPU resources, you can skip this step and use the **Offline Fallback Cache** in the web interface.

### 4. Launch the Web Application

Start the Streamlit application using module syntax:

```bash
python -m streamlit run app.py
```

Once executed, open your browser and navigate to:
```text
http://localhost:8501
```

---

## 🧪 Evaluation & Reviewer Instructions (Section 4 & Section 7)

For course evaluators, teaching assistants, and peer reviewers assessing reproducibility:

1. **Testing Without Hardware / Model Setup**:
   - Open the web interface at `http://localhost:8501`.
   - Navigate to **"📸 现场排队拍照估算 (Queue Estimator)"**.
   - Check the box **"使用离线测试缓存 (用于模拟断网/无本地模型环境)"**.
   - Upload any sample canteen queue image or photograph and click **"开始视觉估算"**.
   - The application will output deterministic headcount, congestion level, and waiting time evaluations immediately.

2. **Testing Live Multimodal Inference**:
   - Uncheck the fallback option.
   - Ensure `ollama run llava` has been triggered in the background.
   - Upload an image taken near dining stalls (e.g., Maxim's Canteen, Chong Yuet Ming Bistro).
   - Click **"开始视觉估算"** to watch the local VLM parse density and compute real-time queue delay on your machine.

---

## 📂 Project Structure

```text
.
├── app.py              # Main Streamlit web application & Ollama orchestration
├── requirements.txt    # Python dependency specifications
└── README.md           # Documentation, architecture guide, and evaluation instructions
```

---

## 📄 License & Course Attribution

Developed for **AILT9019** at The University of Hong Kong (HKU). Provided for academic and research evaluation purposes.