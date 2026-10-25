"""
Test script to verify Bailian (qwen3.8-flash) API connectivity and VLM capability.
Usage: set DASHSCOPE_API_KEY environment variable, then run:
    python test_bailian_vlm.py <path-to-image>
"""
import os
import sys
import base64
import io
from PIL import Image
from openai import OpenAI

API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
BASE_URL = os.getenv(
    "DASHSCOPE_BASE_URL",
    "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
)
MODEL = "qwen3.8-flash"


def compress_image(image_path: str) -> str:
    img = Image.open(image_path)
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.thumbnail((800, 800), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def test_text_only():
    print("--- Text-only test ---")
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "Say hello in exactly 3 words."}],
        max_tokens=20,
        timeout=15,
    )
    print("Response:", resp.choices[0].message.content.strip())


def test_vlm(image_path: str):
    print("\n--- VLM image test ---")
    img_b64 = compress_image(image_path)
    print(f"Compressed image to base64 ({len(img_b64)} chars)")

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    data_url = f"data:image/jpeg;base64,{img_b64}"
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": (
                    "You are a campus dining traffic assistant. Look at this photo of a "
                    "university canteen queue and estimate how many people are visible waiting "
                    "in line. Also assess the crowd density. "
                    "Strictly reply in this format:\n"
                    "PEOPLE_COUNT: <integer>, DENSITY: <Low/Medium/High>"
                )},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        }],
        max_tokens=50,
        timeout=25,
    )
    print("Response:", resp.choices[0].message.content.strip())


if __name__ == "__main__":
    if not API_KEY:
        print("ERROR: DASHSCOPE_API_KEY environment variable is not set.")
        sys.exit(1)

    try:
        test_text_only()
    except Exception as e:
        print("Text-only test FAILED:", type(e).__name__, str(e))

    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        if not os.path.exists(image_path):
            print(f"ERROR: Image file not found: {image_path}")
            sys.exit(1)
        try:
            test_vlm(image_path)
        except Exception as e:
            print("VLM test FAILED:", type(e).__name__, str(e))
    else:
        print("\nNo image path provided, skipping VLM test.")
