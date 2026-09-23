# -*- coding: utf-8 -*-
"""OGP画像（1200x630）を作る。文字がはみ出さないことを測って確認する。"""
from PIL import Image, ImageDraw, ImageFont
import sys

F = "C:/Users/marar/AppData/Local/Microsoft/Windows/Fonts/ZenMaruGothic-%s.ttf"
W, H, PAD = 1200, 630, 74
LINES = ["無料の算数アプリ115本を、学習指導要領の系統にならべました。",
         "単元を押すとアプリが開き、つまずいた子には「戻る先」が出ます。"]
FOOT = "特別支援教材開発研究所（TKK）の無料アプリへのリンク集"
GRADES = ["1年", "2年", "3年", "4年", "5年", "6年", "中学へ"]

im = Image.new("RGB", (W, H), "#ffffff")
d = ImageDraw.Draw(im)
d.rectangle([0, 0, W, 14], fill="#2b5c8a")
bold = ImageFont.truetype(F % "Bold", 78)
med = ImageFont.truetype(F % "Medium", 30)
sm = ImageFont.truetype(F % "Medium", 26)

over = []
def put(x, y, t, f, fill):
    d.text((x, y), t, font=f, fill=fill)
    right = x + d.textlength(t, font=f)
    if right > W - PAD + 2:
        over.append((t[:24], round(right)))

put(PAD, 118, "小学校算数", bold, "#1f2429")
put(PAD, 214, "アプリ系統表", bold, "#2b5c8a")
for i, t in enumerate(LINES):
    put(PAD, 342 + i * 44, t, med, "#41505e")

x = PAD
for g in GRADES:
    w = int(d.textlength(g, font=sm)) + 40
    d.rounded_rectangle([x, 452, x + w, 506], radius=12, outline="#8fa3b8", width=2, fill="#f4f7fa")
    d.text((x + 20, 466), g, font=sm, fill="#173a5e")
    x += w + 12
if x - 12 > W - PAD:
    over.append(("学年チップの帯", x - 12))
put(PAD, 552, FOOT, sm, "#6b7480")

if over:
    print("はみ出し:", over, file=sys.stderr)
    sys.exit(1)
im.save("ogp.png", optimize=True)
print(f"OK ogp.png {im.size} 右端の余白 {W - PAD}px 以内")
