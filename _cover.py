# -*- coding: utf-8 -*-
"""note の見出し画像（1280x670）。3案つくって、はみ出しを測る。

  python _cover.py          3案を scratchpad に出す
  python _cover.py A out.png  選んだ案だけ保存する
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

F = "C:/Users/marar/AppData/Local/Microsoft/Windows/Fonts/ZenMaruGothic-%s.ttf"
W, H = 1280, 670
CREAM, WHITE, INK, MUTE, SUB = "#f4ece0", "#ffffff", "#1f2429", "#6b7480", "#41505e"
ACC, NAVY, LINE = "#2b5c8a", "#22496e", "#cdd3da"
f = lambda w, s: ImageFont.truetype(F % w, s)


class C:
    def __init__(s, bg):
        s.im = Image.new("RGB", (W, H), bg); s.d = ImageDraw.Draw(s.im); s.bad = []; s.box = []

    def panel(s, m, r=30, fill=WHITE):
        s.d.rounded_rectangle([m, m, W - m, H - m], radius=r, fill=fill); s.lim = (m + 56, W - m - 56)

    def t(s, x, y, txt, fo, fill, right=None):
        s.d.text((x, y), txt, font=fo, fill=fill)
        b = s.d.textbbox((x, y), txt, font=fo); s.box.append((txt, b))
        if b[2] > (right or s.lim[1]) + 1: s.bad.append(("右にはみ出し", txt[:16], round(b[2])))
        if b[1] < 44 or b[3] > H - 44: s.bad.append(("上下にはみ出し", txt[:16], b[1], b[3]))
        return b[2] - b[0]

    def tc(s, y, txt, fo, fill):
        w = s.d.textlength(txt, font=fo)
        return s.t((W - w) / 2, y, txt, fo, fill)

    def stack(s, top, bottom, items):
        """items=(文字, フォント, 色, 前の行とのあき)。実寸で積んで、上下の真ん中に置く"""
        hs = [s.d.textbbox((0, 0), t, font=fo) for t, fo, _, _ in items]
        total = sum(b[3] - b[1] for b in hs) + sum(g for *_, g in items[1:])
        y = top + (bottom - top - total) / 2
        for (t, fo, c, g), b in zip(items, hs):
            y += g
            s.tc(y - b[1], t, fo, c)
            y += b[3] - b[1]

    def save(s, p):
        for i in range(len(s.box)):                      # 文字どうしが重なっていないか実測
            for j in range(i + 1, len(s.box)):
                (t1, a), (t2, b) = s.box[i], s.box[j]
                if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                    s.bad.append(("重なり", t1[:12], t2[:12]))
        if s.bad: print("  " + repr(s.bad), file=sys.stderr); return False
        s.im.save(p, optimize=True); return True


def grid(c, gx, gy, cw=78, ch=50, gap=9):
    """学年×系統のマス目。右のマスから、同じ行を左へさかのぼる矢印を引く"""
    cols, rows, hot = 5, 3, 1                      # hot = 矢印を引く行
    lab = f("Bold", 19)
    for i, g in enumerate(["1年", "2年", "3年", "4年", "5年"]):
        x = gx + i * (cw + gap)
        c.d.text((x + (cw - c.d.textlength(g, font=lab)) / 2, gy - 32), g, font=lab, fill=MUTE)
    tint = ["#eef3f8", "#eef6ee", "#fbf5e8"]
    for r in range(rows):
        for i in range(cols):
            x, y = gx + i * (cw + gap), gy + r * (ch + gap)
            if r == hot and i == 4:   fill = ACC              # いま見ている単元
            elif r == hot and i in (2, 3): fill = "#f7f9fb"   # 矢印が通るので薄く
            else: fill = tint[r]
            c.d.rounded_rectangle([x, y, x + cw, y + ch], radius=9, fill=fill)
    y = gy + hot * (ch + gap) + ch / 2
    x1 = gx + 1 * (cw + gap) + cw                  # 戻る先（2年）の右端
    x2 = gx + 4 * (cw + gap)                       # いま見ている単元（5年）の左端
    c.d.line([(x1 + 22, y), (x2 - 4, y)], fill=ACC, width=5)
    c.d.polygon([(x1 + 4, y), (x1 + 24, y - 11), (x1 + 24, y + 11)], fill=ACC)
    c.d.rounded_rectangle([gx + 1 * (cw + gap), gy + hot * (ch + gap),
                           x1, gy + hot * (ch + gap) + ch], radius=9, outline=ACC, width=4)


def A(bg=CREAM):
    c = C(bg); c.panel(40)
    x = 96
    c.t(x, 150, "小学校算数", f("Black", 68), INK)
    c.t(x, 238, "アプリ系統表", f("Black", 68), ACC)
    c.t(x, 360, "無料アプリ115本を、学年と単元で引けます。", f("Medium", 27), SUB, 700)
    c.t(x, 406, "どこまで戻ればいいかも、一緒に出ます。", f("Medium", 27), SUB, 700)
    c.t(x, 505, "特別支援教材開発研究所（TKK）のアプリを、学習指導要領の系統にならべました", f("Medium", 20), MUTE)
    grid(c, 760, 212)
    return c


def B(bg=NAVY):
    c = C(bg); c.panel(40)
    c.stack(40, H - 40, [
        ("小学校算数の無料アプリ", f("Black", 50), INK, 0),
        ("115本", f("Black", 168), ACC, 26),
        ("学年と単元から探せるように、ならべました。", f("Medium", 28), SUB, 40),
        ("つまずいた子は、どこまで戻ればいいかまで分かります。", f("Medium", 28), SUB, 16),
        ("特別支援教材開発研究所（TKK）", f("Medium", 20), MUTE, 34),
    ])
    return c


def Cc():
    c = C(CREAM); c.panel(40)
    x = 96
    c.t(x, 118, "「わり算ができない」", f("Black", 70), INK)
    c.t(x, 230, "九九？　ひき算の筆算？　意味？", f("Black", 44), ACC)
    c.d.line([(x, 344), (W - 96, 344)], fill=LINE, width=2)
    c.t(x, 382, "どこからどこでつまずいているのかを、見取るための表です。", f("Medium", 30), SUB)
    c.t(x, 464, "小学校算数 アプリ系統表", f("Black", 40), INK)
    c.t(x, 534, "特別支援教材開発研究所（TKK）の無料アプリ115本へのリンク集", f("Medium", 21), MUTE)
    return c



def D(bg=NAVY):
    """マス目と数字の両方を入れた案"""
    c = C(bg); c.panel(40)
    x = 96
    c.t(x, 128, "小学校算数 アプリ系統表", f("Black", 52), INK, 700)
    w = c.t(x - 4, 208, "115", f("Black", 124), ACC, 700)
    c.t(x - 4 + w + 8, 268, "本", f("Black", 50), INK, 700)
    c.t(x, 388, "無料の算数アプリを、学年と単元で引けます。", f("Medium", 26), SUB, 700)
    c.t(x, 432, "どこまで戻ればいいかも、一緒に出ます。", f("Medium", 26), SUB, 700)
    c.t(x, 512, "特別支援教材開発研究所（TKK）のアプリを、学習指導要領の系統にならべました", f("Medium", 20), MUTE)
    grid(c, 760, 212)
    return c

V = {"A": A, "B": B, "C": Cc,
     "1": lambda: A(CREAM), "2": lambda: A(NAVY),
     "3": lambda: B(CREAM), "4": lambda: B(NAVY), "5": lambda: D(NAVY)}
if len(sys.argv) > 2 and not any(a.startswith("--round") for a in sys.argv):
    ok = V[sys.argv[1]]().save(sys.argv[2]); print(("OK " if ok else "NG ") + sys.argv[2]); sys.exit(0 if ok else 1)
out = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
bad = 0
keys = ["2", "4", "5"] if "--round3" in sys.argv else (["1", "2", "3", "4"] if "--round2" in sys.argv else ["A", "B", "C"])
for k in keys:
    fn = V[k]
    q = out / f"cover_{k}.png"
    ok = fn().save(q); print(f"[{k}]", "OK" if ok else "NG", q); bad += 0 if ok else 1
sys.exit(1 if bad else 0)
