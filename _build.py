# -*- coding: utf-8 -*-
"""
算数アプリ系統表（TKK）ビルド
  keito.json（系統表＋アプリ当てはめ）
  _src/tkk_articles_full.json（tkk-fk.com の記事一覧・アプリ直リンク。スクレイプ結果）
  _template.html
  → index.html と 算数アプリ系統表.html（同一内容）
"""
import json, re, shutil, sys, urllib.parse
from pathlib import Path

HERE = Path(__file__).parent
keito = json.loads((HERE / "keito.json").read_text(encoding="utf-8"))
arts = json.loads((HERE / "_src" / "tkk_articles_full.json").read_text(encoding="utf-8"))

# 同梱フォント(Zen Maru Gothic)に無い字は、形の近い字へ置き換える（1字だけ別フォントになるのを防ぐ）
FONT_SUB = {"―": "—"}  # ― → —

def clean_title(t):
    t = re.sub(r"^(?:【作成中】|作成中)?(?:【[^】]+】)+", "", t).strip()
    for a, b in FONT_SUB.items():
        t = t.replace(a, b)
    return t

def find(key):
    if key.startswith("t:"):
        q = key[2:]
        hits = [a for a in arts if q in a["title"]]
    else:
        hits = [a for a in arts if urllib.parse.unquote(a["url"]).rstrip("/").endswith("/" + key)]
    if len(hits) != 1:
        print(f"!! key '{key}' -> {len(hits)} hits", file=sys.stderr)
        return None
    a = hits[0]
    full = clean_title(a["title"])
    main, _, sub = full.partition("｜")
    if not sub:
        main, _, sub = full.partition("　")
    return {
        "id": key,
        "name": main.strip(),
        "sub": sub.strip(),
        "app": a["apps"][0] if a["apps"] else "",
        "article": a["url"],
        "wip": "作成中" in a["title"],
        "d3": "３Dプリント" in a["title"] or "3Dプリント" in a["title"],
    }

apps = {}
missing = []
def reg(key):
    if key in apps:
        return
    a = find(key)
    if a: apps[key] = a
    else: missing.append(key)

for g in keito["groups"]:
    for r in g["rows"]:
        for grade, chips in r["cells"].items():
            for ch in chips:
                for k in ch["apps"]:
                    reg(k)
for it in keito["tools"]["items"]:
    for k in it["apps"]:
        reg(k)

if missing:
    print("未解決キー:", missing, file=sys.stderr)
    sys.exit(1)

data = {"grades": keito["grades"], "groups": keito["groups"], "tools": keito["tools"], "apps": apps}
n_apps = len(apps)
n_chips = sum(len(chips) for g in keito["groups"] for r in g["rows"] for chips in r["cells"].values())

tpl = (HERE / "_template.html").read_text(encoding="utf-8")
html = tpl.replace("/*__DATA__*/", json.dumps(data, ensure_ascii=False))
html = html.replace("__NAPPS__", str(n_apps)).replace("__NCHIPS__", str(n_chips))
(HERE / "index.html").write_text(html, encoding="utf-8")
# 日本語名の配布用コピー（中身は同じ）。検索エンジンには index.html を正とみなしてもらう
NOINDEX = '<meta name="robots" content="noindex">' + chr(10) + '<link rel="canonical"'
(HERE / "算数アプリ系統表.html").write_text(
    html.replace('<link rel="canonical"', NOINDEX, 1), encoding="utf-8")
print(f"OK apps={n_apps} chips={n_chips} -> index.html / 算数アプリ系統表.html")
