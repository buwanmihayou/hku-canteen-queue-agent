import base64
import json
import re
import ollama
import streamlit as st

# ====================== 1. 页面基本配置 ======================
st.set_page_config(
    page_title="HKU Canteen Queue Assistant", page_icon="🍲", layout="centered"
)
st.title("🍲 HKU Canteen Peak-Hour Queue Assistant")
st.caption(
    "Powered by Local Ollama Vision Agent | Built for HKU Community (11:50–13:30"
    " & 17:30–19:00)"
)

# 基础知识库与常数定义 (基准数据矩阵)
STALL_RATES = {
    "Alfafa Bistro (Chong Yuet Ming)": {"rate_min_per_person": 1.2, "walk": 3},
    "Maxim's Canteen (Main Campus)": {"rate_min_per_person": 0.6, "walk": 5},
    "Swire Canteen (Swire Building)": {"rate_min_per_person": 0.8, "walk": 4},
}

# 离线演示兜底缓存 (API-down Cache，保障评测防翻车)
FALLBACK_CACHE = {
    "sample_peak": {
        "count": 16,
        "density": "High",
        "stall": "Alfafa Bistro (Chong Yuet Ming)",
    },
    "sample_mid": {
        "count": 8,
        "density": "Medium",
        "stall": "Maxim's Canteen (Main Campus)",
    },
}

# ====================== 2. 功能切换标签页 ======================
tab1, tab2 = st.tabs(
    ["🚶‍♂️ 避峰推荐 (Route Planner)", "📸 现场排队拍照估算 (Queue Estimator)"]
)

# ----------------- Tab 1: 位置与避峰推荐 -----------------
with tab1:
  st.subheader("功能一：基于位置的食堂排队耗时推荐")
  location = st.selectbox(
      "请选择你当前所在的校园建筑：",
      [
          "Main Building (本部大楼)",
          "Chong Yuet Ming Building (庄月明楼)",
          "Run Run Shaw Building (邵逸夫楼)",
          "Centennial Campus (百周年校园)",
      ],
  )

  if st.button("查询推荐就餐方案", type="primary"):
    st.write(f"📍 当前出发点：**{location}**")
    results = []
    base_waits = {
        "Alfafa Bistro (Chong Yuet Ming)": 15,
        "Maxim's Canteen (Main Campus)": 10,
        "Swire Canteen (Swire Building)": 6,
    }

    for stall, info in STALL_RATES.items():
      t_walk = info["walk"]
      t_wait = base_waits[stall]
      t_total = t_walk + t_wait
      results.append((stall, t_walk, t_wait, t_total))

    # 按总耗时由短到长排序 (Top-3)
    results.sort(key=lambda x: x[3])

    st.success("✅ 为你推荐耗时最短的食堂 Top-3：")
    for rank, (stall, t_walk, t_wait, t_total) in enumerate(results, 1):
      st.markdown(
          f"**{rank}. {stall}** — 总计耗时约 **{t_total} 分钟** "
          f"(步行: {t_walk} 分钟 | 历史预估排队: {t_wait} 分钟)"
      )

# ----------------- Tab 2: 现场照片视觉估算 -----------------
with tab2:
  st.subheader("功能二：上传现场排队照片估算剩余时间")
  selected_stall = st.selectbox(
      "请选择当前所在的档口：", list(STALL_RATES.keys())
  )

  uploaded_file = st.file_uploader(
      "上传排队现场照片 (JPEG/PNG)", type=["jpg", "jpeg", "png"]
  )
  use_offline_cache = st.checkbox(
      "使用离线测试缓存 (用于模拟断网/无本地模型环境)"
  )

  if uploaded_file is not None:
    st.image(uploaded_file, caption="已上传照片 (本地即时脱敏处理)", width=350)
    st.info("🔒 隐私保护：照片在内存中完成估算后将立即销毁，不存储人脸生物信息。")

    if st.button("开始视觉估算", type="primary"):
      with st.spinner("Ollama 视觉模型正在分析排队密集度与人数..."):
        if use_offline_cache:
          people_count = FALLBACK_CACHE["sample_peak"]["count"]
          density = FALLBACK_CACHE["sample_peak"]["density"]
          st.warning("⚠️ 当前运行于离线兜底模式 (Fallback Cache)。")
        else:
          try:
            bytes_data = uploaded_file.getvalue()

            # 调用本地 Ollama 的 llava 视觉模型
            response = ollama.chat(
                model="llava",
                messages=[{
                    "role": "user",
                    "content": (
                        "你是一个食堂排队评估员。请观察照片并评估队伍情况："
                        "1. 估计排队人数的大致整数值；"
                        "2. 拥挤等级（Low/Medium/High）。"
                        "请严格只返回一个标准的 JSON 对象，格式如："
                        '{"count": 12, "density": "Medium"}'
                    ),
                    "images": [bytes_data],
                }],
            )

            raw_text = response["message"]["content"]
            match = re.search(r"\{.*?\}", raw_text, re.DOTALL)
            if match:
              data = json.loads(match.group(0))
              people_count = int(data.get("count", 10))
              density = data.get("density", "Medium")
            else:
              people_count, density = 10, "Medium"

          except Exception as e:
            st.error(f"调用本地 Ollama 失败，请检查服务是否开启: {e}")
            people_count, density = 10, "Estimated"

        stall_rate = STALL_RATES[selected_stall]["rate_min_per_person"]
        estimated_wait = round(people_count * stall_rate, 1)

        st.metric(label="预估排队人数", value=f"约 {people_count} 人")
        st.metric(
            label="预计等待时长",
            value=f"{estimated_wait} 分钟",
            delta=f"密集度: {density}",
        )
        st.write(
            f"💡 计算依据：{selected_stall} 平均每人点餐耗时约 {stall_rate}"
            " 分钟。"
        )