"""Build a self-contained offline planner and installable PWA assets."""
from datetime import time
import hashlib
import json
from pathlib import Path
import shutil

from PIL import Image, ImageDraw
from calibration import STALL_RATES, estimated_queue_count
from routing import WALK_TIMES

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "offline"


def export_data():
    return {
        "schema_version": 1,
        "timezone": "Asia/Hong_Kong",
        "basis": "Empirical assumptions; not live queues or measured calibration.",
        "canteens": [
            {"name": name, "rate": info["rate_min_per_person"],
             "counts": [estimated_queue_count(name, time(m // 60, m % 60)) for m in range(1440)]}
            for name, info in STALL_RATES.items()
        ],
        "walk_times": WALK_TIMES,
    }


def build(output=OUTPUT):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    if output.resolve() != OUTPUT.resolve():
        shutil.copyfile(OUTPUT / "manifest.webmanifest", output / "manifest.webmanifest")
    for size in (192, 512):
        icon = Image.new("RGB", (size, size), "#143a32")
        draw = ImageDraw.Draw(icon)
        draw.arc((size * .2, size * .2, size * .8, size * .85), 0, 180,
                 fill="#f4f6f1", width=round(size * .08))
        draw.line((size * .17, size * .525, size * .83, size * .525),
                  fill="#f4f6f1", width=round(size * .06))
        for x in (.36, .5, .64):
            draw.line((size * x, size * .22, size * x, size * .37),
                      fill="#d09b48", width=round(size * .035))
        icon.save(output / f"icon-{size}.png")
    data = json.dumps(export_data(), ensure_ascii=False, separators=(",", ":"))
    page = (OUTPUT / "template.html").read_text(encoding="utf-8")
    for marker, filename in [("STYLE", "style.css"), ("CORE", "planner.js"), ("SCRIPT", "app.js")]:
        page = page.replace(f"%%{marker}%%", (OUTPUT / filename).read_text(encoding="utf-8"))
    page = page.replace("%%DATA%%", data.replace("<", "\\u003c"))
    (output / "data.json").write_text(data + "\n", encoding="utf-8")
    standalone = page.replace("%%MANIFEST%%", "").replace("%%REGISTER%%", "")
    standalone = "\n".join(line.rstrip() for line in standalone.splitlines()) + "\n"
    (output / "offline.html").write_text(standalone, encoding="utf-8")
    register = (OUTPUT / "register.js").read_text(encoding="utf-8")
    online = page.replace("%%MANIFEST%%", '<link rel="manifest" href="manifest.webmanifest">')
    (output / "index.html").write_text(online.replace("%%REGISTER%%", f"<script>{register}</script>"), encoding="utf-8")
    digest = hashlib.sha256()
    for name in ["index.html", "offline.html", "data.json", "manifest.webmanifest", "icon-192.png", "icon-512.png"]:
        digest.update((output / name).read_bytes())
    worker = (OUTPUT / "sw-template.js").read_text(encoding="utf-8")
    (output / "sw.js").write_text(worker.replace("%%VERSION%%", digest.hexdigest()[:16]), encoding="utf-8")
    return output


if __name__ == "__main__":
    print(f"Built standalone offline.html and PWA assets in {build()}")
