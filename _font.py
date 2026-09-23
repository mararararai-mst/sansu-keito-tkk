# -*- coding: utf-8 -*-
"""同梱フォント（Zen Maru Gothic のサブセット）を作り直す

公開ページは Zen Maru Gothic が入っていない端末でも同じ字形で出したいので、
表で使っている字だけに絞った woff2 を font/ に同梱している。
文言を足して新しい字が増えたら、これを流さないとその字だけ別フォントになる。

  python _font.py          ビルド済みの3枚から字を集めて作り直す
  python _font.py --check  足りない字があるかだけ見る（作り直さない）

元フォントは本人PCにインストール済みのものを使う（SIL OFL。font/OFL.txt）。
"""
import re, sys
from pathlib import Path
from fontTools import subset
from fontTools.ttLib import TTFont

HERE = Path(__file__).parent
PAGES = ["index.html", "kokugo.html", "jiritsu.html"]
SRC = Path.home() / "AppData/Local/Microsoft/Windows/Fonts"
WEIGHTS = {"Medium": "ZenMaruGothic-Medium", "Bold": "ZenMaruGothic-Bold"}


def used_chars():
    s = set()
    for f in PAGES:
        p = HERE / f
        if p.exists():
            t = p.read_text(encoding="utf-8")
            t = re.sub(r"<style[\s\S]*?</style>", "", t)          # CSS は字として出ない
            s |= set(t)
    s |= {chr(c) for c in range(0x20, 0x7F)}                        # 英数字は常に入れておく
    return {c for c in s if c.isprintable() and not c.isspace() or c == " "}


def main():
    chars = used_chars()
    out = HERE / "font"
    bad = 0
    for w, stem in WEIGHTS.items():
        cur = TTFont(out / f"{stem}.subset.woff2").getBestCmap()
        lack = sorted(c for c in chars if ord(c) not in cur and ord(c) > 0x7F)
        src = SRC / f"{stem}.ttf"
        full = TTFont(src).getBestCmap() if src.exists() else {}
        nofont = [c for c in lack if full and ord(c) not in full]
        print(f"[{w}] 使っている字 {len(chars)} / 同梱に無い字 {len(lack)}: {''.join(lack)[:60]}")
        if nofont:
            print(f"      ※元フォント自体に無い字（別の字に置き換えるか図にする）: {''.join(nofont)}")
        bad += len(lack)          # 元フォントに無い字も、その字だけ別フォントになるので不合格
        if "--check" in sys.argv:
            continue
        if not src.exists():
            print(f"      元フォントが見つからない: {src}"); sys.exit(2)
        opt = subset.Options()
        opt.flavor = "woff2"
        opt.layout_features = ["*"]
        opt.name_IDs = ["*"]
        opt.notdef_outline = True
        f = TTFont(src)
        sub = subset.Subsetter(opt)
        sub.populate(unicodes=[ord(c) for c in chars if ord(c) in f.getBestCmap()])
        sub.subset(f)
        dst = out / f"{stem}.subset.woff2"
        f.flavor = "woff2"
        f.save(dst)
        print(f"      → {dst.name} {dst.stat().st_size // 1024}KB")
    if "--check" in sys.argv and bad:
        sys.exit(1)


main()
