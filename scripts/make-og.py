"""生成分享卡片图 public/og.png（1200x630，浅色）"""

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "og.png"

BG = (251, 251, 249)
FG = (27, 27, 25)
DIM = (88, 88, 84)
MUTE = (146, 146, 140)
LINE = (231, 231, 228)

NAME = os.environ.get("OG_NAME", "你的名字")
ROLE = os.environ.get("OG_ROLE", "游戏客户端开发工程师")
NOTE = os.environ.get("OG_NOTE", "作品集 · 战斗系统 · 性能优化 · 演示视频")

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
]


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    paths = FONT_CANDIDATES if bold else FONT_CANDIDATES[1:] + FONT_CANDIDATES[:1]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return ImageFont.load_default()


img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

# 细网格
for x in range(0, W, 48):
    draw.line([(x, 0), (x, H)], fill=LINE)
for y in range(0, H, 48):
    draw.line([(0, y), (W, y)], fill=LINE)

# 右侧同心圆
cx, cy = int(W * 0.78), int(H * 0.46)
for i in range(6):
    r = 70 + i * 58
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(222, 222, 217), width=1)
draw.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=FG)

# 边框
draw.rectangle([0, 0, W - 1, H - 1], outline=(227, 227, 222), width=1)

f_name = load_font(76, bold=True)
f_role = load_font(26)
f_note = load_font(20)
f_small = load_font(18)

x0 = 80
y = 176

draw.text((x0, y), NAME, font=f_name, fill=FG)
box = draw.textbbox((x0, y), NAME, font=f_name)
name_bottom = box[3]

draw.text((x0, name_bottom + 22), ROLE, font=f_role, fill=DIM)
draw.text((x0, name_bottom + 72), NOTE, font=f_note, fill=MUTE)

draw.line([(x0, H - 104), (W - x0, H - 104)], fill=LINE)
draw.text((x0, H - 82), "PORTFOLIO", font=f_small, fill=MUTE)
right = "works / stack / contact"
rw = draw.textlength(right, font=f_small)
draw.text((W - x0 - rw, H - 82), right, font=f_small, fill=MUTE)

OUT.parent.mkdir(parents=True, exist_ok=True)
img.save(OUT, "PNG", optimize=True)
print(f"[ok] {OUT}  ({OUT.stat().st_size / 1024:.0f} KB)")
