import os
import re
import io
import base64
from PIL import Image
import streamlit as st

from routing import rank_canteens

# ==========================================
# Page Configuration
# ==========================================
st.set_page_config(
    page_title="HKU Canteen Queue Assistant",
    page_icon="🍲",
    layout="centered"
)

# ==========================================
# Retrieve & Clean Bailian API Configuration
# ==========================================
def _safe_get_secret(key, env_default=None):
    """Read from Streamlit secrets if available; otherwise fall back to env vars.

    Local runs without a secrets.toml file raise StreamlitSecretNotFoundError,
    so we catch that and read from the environment instead.
    """
    try:
        return st.secrets.get(key, os.getenv(key, env_default or ""))
    except Exception:
        return os.getenv(key, env_default or "")


raw_bailian_key = _safe_get_secret("DASHSCOPE_API_KEY")
BAILIAN_KEY = (
    str(raw_bailian_key)
    .replace("\n", "")
    .replace("\r", "")
    .replace(" ", "")
    .strip()
    if raw_bailian_key
    else None
)

raw_base_url = _safe_get_secret(
    "DASHSCOPE_BASE_URL",
    "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
)
BAILIAN_BASE_URL = (
    str(raw_base_url).strip().rstrip("/")
    if raw_base_url
    else "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
)

# ==========================================
# HKU Dining & Transit Knowledge Base
# ==========================================
STALL_RATES = {
    "CYM Canteen (Chong Yuet Ming Cultural Centre)": {"rate_min_per_person": 1.2},
    "JuYing Tai (Fong Shu Chuen Amenities Centre, Swire Building)": {"rate_min_per_person": 0.6},
    "Union Restaurant (Haking Wong Building)": {"rate_min_per_person": 0.8},
    "alfafa bistro (Jockey Club Tower, Centennial Campus)": {"rate_min_per_person": 1.0},
    "TAI TAI FOODTOPIA (Composite Building)": {"rate_min_per_person": 0.7},
}

CAMPUS_LOCATIONS = [
    "Main Building",
    "Chong Yuet Ming Cultural Centre",
    "Run Run Shaw Building",
    "Centennial Campus (Grand Hall)",
    "Haking Wong Building",
    "Knowles Building",
]

# ==========================================
# Core LLM Reasoning (Alibaba Cloud Bailian)
# ==========================================
def call_bailian_llm(prompt, max_tokens=150):
    """Call course-sponsored Qwen3.8-Flash model via OpenAI-compatible endpoint (text-only)."""
    if not BAILIAN_KEY:
        return None, "API key not configured"

    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=BAILIAN_KEY,
            base_url=BAILIAN_BASE_URL
        )
        response = client.chat.completions.create(
            model="qwen3.8-flash",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            timeout=12
        )
        return response.choices[0].message.content, None
    except Exception as e:
        return None, f"Bailian API error: {str(e)}"


def call_bailian_vlm(prompt, image_base64, max_tokens=80):
    """Call Qwen3.8-Flash with multimodal (text + image) input via OpenAI-compatible endpoint."""
    if not BAILIAN_KEY:
        return None, "API key not configured"

    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=BAILIAN_KEY,
            base_url=BAILIAN_BASE_URL
        )
        data_url = f"data:image/jpeg;base64,{image_base64}"
        response = client.chat.completions.create(
            model="qwen3.8-flash",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }],
            max_tokens=max_tokens,
            timeout=20
        )
        return response.choices[0].message.content, None
    except Exception as e:
        return None, f"Bailian VLM error: {str(e)}"

# ==========================================
# Queue Estimation Pipeline
# ==========================================
def analyze_queue_image(image_file, use_offline_cache=False):
    """
    Queue Estimation Pipeline:
    1. Returns deterministic benchmark data if offline test cache is selected.
    2. Compresses the uploaded image in-memory, encodes to base64, and sends it
       as a multimodal (image + text) request to Qwen3.8-Flash for true VLM inference.
    3. Guarantees deterministic fallback execution without external API failure risks.
    All image processing is ephemeral — nothing is persisted to disk.
    """
    # Mode 1: Offline benchmark cache
    if use_offline_cache:
        return 16, "High", "AILT9019 Benchmark Test Cache"

    # Mode 2: Live VLM — compress image and send to Qwen3.8-Flash
    try:
        img = Image.open(image_file)
        if img.mode != "RGB":
            img = img.convert("RGB")
        # Compress to max 800x800, JPEG quality 80 (keeps payload small for API)
        img.thumbnail((800, 800), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=80)
        img_bytes = buffer.getvalue()
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")
    except Exception:
        return 8, "Medium", "Empirical Fallback"

    prompt = (
        "You are a campus dining traffic assistant. Look at this photo of a university "
        "canteen queue and estimate how many people are visible waiting in line. "
        "Also assess the crowd density. "
        "Strictly reply in this format without any additional conversational text:\n"
        "PEOPLE_COUNT: <integer>, DENSITY: <Low/Medium/High>"
    )

    llm_res, err = call_bailian_vlm(prompt, img_base64, max_tokens=50)

    if err:
        return 8, "Medium", f"AILT9019 Empirical Fallback ({err})"

    if llm_res:
        match = re.search(r"PEOPLE_COUNT:\s*(\d+)", llm_res)
        if match:
            count = int(match.group(1))
        else:
            digit_match = re.search(r"\d+", llm_res)
            count = int(digit_match.group()) if digit_match else 8

        density_match = re.search(r"DENSITY:\s*(\w+)", llm_res, re.IGNORECASE)
        if density_match:
            density = density_match.group(1).capitalize()
        else:
            density = "High" if count > 15 else ("Medium" if count > 6 else "Low")
        return count, density, "Alibaba Bailian VLM (Qwen3.8-Flash)"

    return 8, "Medium", "AILT9019 Empirical Fallback"


# ==========================================
# Streamlit UI
# ==========================================
st.title("🍲 HKU Canteen Queue Assistant")
st.caption("AI-driven multi-modal dining assistant for HKU students | Course Project (AILT9019)")

tab1, tab2 = st.tabs(["🚶‍♂️ Transit & Peak Planner", "📷 Live Queue Estimator"])

# ------------------------------------------
# Tab 1: Transit & Peak Planner
# ------------------------------------------
with tab1:
    st.subheader("1. Campus Transit & Route Optimization")
    user_location = st.selectbox(
        "Select your current campus location:",
        CAMPUS_LOCATIONS,
        key="tab1_location"
    )
    urgency = st.radio(
        "Time constraint / Urgency:",
        ["In a Rush (Prioritize short walk)", "Regular Dining (Balanced transit & wait)"],
        horizontal=True,
        key="tab1_urgency"
    )

    if st.button("Find Optimal Dining Route", type="primary", key="tab1_btn"):
        st.markdown("### Recommended Dining Plans:")
        ranked = rank_canteens(
            STALL_RATES,
            user_location,
            prioritize_short_walk="Rush" in urgency,
        )
        top_canteen, top_walk, top_wait, top_total, _ = ranked[0]

        for idx, (name, walk, wait, total, _) in enumerate(ranked[:3], 1):
            st.success(
                f"**Top {idx} Option: {name}**\n\n"
                f"- Estimated transit walk: ~**{walk}** mins\n"
                f"- Anticipated queue wait: ~**{wait:.1f}** mins\n"
                f"- Total door-to-meal time: ~**{total:.1f}** mins"
            )

        st.caption(
            "Walking times are estimates and may vary due to lifts, stairs, slopes, "
            "entrances, congestion, and walking pace."
        )

        with st.spinner("Generating personalized AI transit advice..."):
            advice_prompt = (
                f"You are a helpful HKU campus guide. A student is currently at [{user_location}] "
                f"with condition [{urgency}]. The best recommended canteen is [{top_canteen}] "
                f"(total time ~{top_total:.1f} mins). Provide 2 concise, practical English sentences "
                "with a specific campus shortcut or dining tip."
            )
            ai_advice, err = call_bailian_llm(advice_prompt, max_tokens=120)
            if ai_advice:
                st.info(f"💡 **AI Campus Transit Advice (Qwen3.8-Flash)**:\n\n{ai_advice}")
            else:
                st.warning(f"⚠️ AI transit advice unavailable: {err or 'Unknown error'}. Showing heuristic tip instead.")
                st.info(f"💡 **Tip**: Head to **{top_canteen}** — ~{top_walk} min walk + ~{top_wait:.1f} min queue = ~{top_total:.1f} min total. Leave a few minutes early to beat the rush.")

# ------------------------------------------
# Tab 2: Live Queue Estimator
# ------------------------------------------
with tab2:
    st.subheader("2. Real-Time Photo Queue Estimation")

    selected_canteen = st.selectbox(
        "Select target dining counter / canteen:",
        list(STALL_RATES.keys()),
        key="tab2_canteen"
    )

    use_cache = st.checkbox(
        "Use benchmark verification cache (Offline test mode)",
        value=False,
        key="tab2_cache"
    )

    uploaded_file = st.file_uploader(
        "Upload queue photograph (JPEG/PNG):",
        type=["jpg", "jpeg", "png"],
        key="tab2_uploader"
    )

    if uploaded_file is not None:
        st.image(
            uploaded_file,
            caption="Uploaded photograph (In-memory ephemeral processing)",
            width="stretch"
        )

        st.info("🔒 **Privacy Safeguard**: Photographs are processed ephemerally in volatile memory for headcount estimation and discarded immediately without logging biometric data.")

        if st.button("Estimate Queue Delays", type="primary", key="tab2_btn"):
            with st.spinner("VLM analyzing queue photo for crowd density & headcount..."):
                people_count, density, source = analyze_queue_image(
                    uploaded_file,
                    use_offline_cache=use_cache
                )

            rate = STALL_RATES[selected_canteen]["rate_min_per_person"]
            est_time = people_count * rate

            st.success(f"✅ Analysis Complete! Engine: {source}")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Estimated Queue Count", f"~{people_count} people")
            with col2:
                st.metric(
                    "Expected Wait Time",
                    f"{est_time:.1f} mins",
                    delta=f"Density: {density}",
                    delta_color="normal"
                )

            st.caption(f"💡 Calculation basis: {selected_canteen} average turnaround is {rate} min/customer.")
