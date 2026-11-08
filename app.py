"""HKU dining planner and photo queue estimator."""

import os
from datetime import datetime
from pathlib import Path

import streamlit as st

from calibration import STALL_RATES, HK_TIMEZONE, estimate_wait_minutes
from queue_analysis import analyze_queue_image
from routing import WALK_TIMES, rank_canteens

st.set_page_config(page_title="HKU Canteen Queue Assistant", page_icon="🍽️", layout="centered")
st.html(Path(__file__).with_name("mobile.css"))


def _safe_get_secret(key, default=""):
    try:
        return st.secrets.get(key, os.getenv(key, default))
    except Exception:
        return os.getenv(key, default)


BAILIAN_KEY = "".join(str(_safe_get_secret("DASHSCOPE_API_KEY") or "").split())
BAILIAN_BASE_URL = str(_safe_get_secret(
    "DASHSCOPE_BASE_URL",
    "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
)).strip().rstrip("/")


def _call_bailian(content, max_tokens, timeout):
    if not BAILIAN_KEY:
        return None, "API key not configured"
    try:
        from openai import OpenAI
        client = OpenAI(api_key=BAILIAN_KEY, base_url=BAILIAN_BASE_URL, max_retries=0)
        response = client.chat.completions.create(
            model="qwen3.8-flash", messages=[{"role": "user", "content": content}],
            max_tokens=max_tokens, timeout=timeout,
        )
        return response.choices[0].message.content, None
    except Exception:
        # Provider exceptions can contain request details; show only a neutral message.
        return None, "AI analysis is temporarily unavailable"


def call_bailian_llm(prompt, max_tokens=150):
    return _call_bailian(prompt, max_tokens, 12)


def call_bailian_vlm(prompt, image_base64, max_tokens=80):
    return _call_bailian([
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
    ], max_tokens, 20)


st.title("🍽️ HKU Canteen Queue Assistant")
st.caption("Dining estimates for HKU students | AILT9019 Group 37")
st.info("Queue forecasts are provisional assumptions, not live measurements or verified calibration.")

offline_page = Path(__file__).with_name("offline") / "offline.html"
if offline_page.is_file():
    st.download_button(
        "Save offline dining calculator", offline_page.read_bytes(),
        file_name="hku-canteen-offline.html", mime="text/html", key="offline_download",
    )
    st.caption("Save before losing connection. Open the saved file for offline routes and manual waits. This Streamlit page itself needs a server connection.")

tab1, tab2 = st.tabs(["Transit & Peak Planner", "Photo Queue Estimator"])

with tab1:
    st.subheader("1. Campus Transit & Route Optimization")
    user_location = st.selectbox("Select your current campus location:", list(WALK_TIMES), key="tab1_location")
    urgency = st.radio(
        "Time constraint / Urgency:",
        ["In a Rush (Prioritize short walk)", "Regular Dining (Balanced transit & wait)"],
        horizontal=True, key="tab1_urgency",
    )
    dining_time = st.time_input(
        "Planned dining time (Hong Kong, UTC+8):",
        value=datetime.now(HK_TIMEZONE).time().replace(second=0, microsecond=0), key="tab1_time",
    )
    st.caption("Queue estimates follow provisional lunch and dinner demand curves. They are not live counts; opening hours are not checked.")

    use_ai_advice = st.checkbox("Request optional cloud dining advice", value=False, key="tab1_ai")
    if st.button("Find Optimal Dining Route", type="primary", key="tab1_btn"):
        ranked = rank_canteens(
            STALL_RATES, user_location,
            prioritize_short_walk="Rush" in urgency, dining_time=dining_time,
        )
        top_canteen, top_walk, top_wait, top_total, _ = ranked[0]
        st.markdown("### Recommended Dining Plans")
        for idx, (name, walk, wait, total, _) in enumerate(ranked[:3], 1):
            st.success(
                f"**Top {idx}: {name}**\n\n"
                f"- Estimated walk: **{walk} min**\n"
                f"- Assumed queue wait: **{wait:.1f} min**\n"
                f"- Total walk and queue: **{total:.1f} min**"
            )
        st.caption("Rush mode gives walking time extra weight when ranking. Displayed totals are walk plus queue. Lifts, stairs, slopes and walking pace can change travel times.")
        ai_advice = None
        if use_ai_advice:
            with st.spinner("Generating campus dining advice..."):
                ai_advice, _ = call_bailian_llm(
                    f"A student at {user_location} prefers {urgency}. Recommend {top_canteen} "
                    f"at {dining_time:%H:%M} Hong Kong time. Estimated walk: {top_walk} minutes; "
                    f"assumed queue: {top_wait:.1f} minutes. Give two short practical English "
                    "sentences. Do not invent shortcuts, opening hours or live queue observations.",
                    max_tokens=120,
                )
        st.info(ai_advice or (
            f"Head to {top_canteen}: about {top_walk} min walk + {top_wait:.1f} min "
            f"assumed queue = {top_total:.1f} min total. Check opening hours before leaving."
        ))

with tab2:
    st.subheader("2. Queue delay estimation")
    selected_canteen = st.selectbox(
        "Select target dining counter / canteen:", list(STALL_RATES), key="tab2_canteen",
    )
    mode = st.radio("Count source", ["Manual count", "Photo estimate (cloud)", "Synthetic demo"],
                    key="tab2_mode")
    count = None
    if mode == "Manual count":
        manual_count = st.number_input("People waiting ahead of you", min_value=0, max_value=10000,
                                       value=8, step=1, key="tab2_manual")
        st.caption("Enter your own observation. The initial value is an example, not a measurement.")
        if st.button("Calculate wait", type="primary", key="tab2_btn"):
            count = int(manual_count)
            st.info("Using your manual count.")
    elif mode == "Synthetic demo":
        st.warning("Demonstration only: 16 synthetic people. This does not analyze a photo or verify accuracy.")
        if st.button("Run synthetic demo", type="primary", key="tab2_btn"):
            result = analyze_queue_image(None, use_offline_cache=True)
            count = result.count
    else:
        uploaded_file = st.file_uploader(
            "Queue photograph (JPEG/PNG, up to 10 MB)",
            type=["jpg", "jpeg", "png"], key="tab2_uploader",
        )
        st.caption("The photo is uploaded to this app's server. On request, a compressed copy is sent to Alibaba Cloud. The app does not save image files to disk; provider retention rules may differ.")
        consent = st.checkbox("Send this photo to the cloud model for headcount estimation",
                              value=False, key="tab2_consent")
        if st.button("Estimate queue delay", type="primary", key="tab2_btn",
                     disabled=uploaded_file is None or not consent):
            try:
                with st.spinner("Estimating the visible queue..."):
                    result = analyze_queue_image(uploaded_file, vlm_call=call_bailian_vlm)
            except ValueError as error:
                st.error(str(error))
            else:
                if result.count is None:
                    st.warning(result.detail)
                    st.info("Select Manual count to continue without the cloud service.")
                else:
                    count = result.count
                    st.info(f"{result.source}. Verify the estimate against a manual count.")
    if count is not None:
        wait = estimate_wait_minutes(selected_canteen, people_count=count)
        with st.container(key="tab2_metrics"):
            col1, col2 = st.columns(2)
            col1.metric("Queue count", f"{count} people")
            col2.metric("Estimated wait", f"{wait:.1f} min")
        rate = STALL_RATES[selected_canteen]["rate_min_per_person"]
        st.caption(f"{count} people x {rate:g} min/person = {wait:.1f} min. Service rates are empirical and unvalidated.")
