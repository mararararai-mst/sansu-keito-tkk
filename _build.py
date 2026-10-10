# -*- coding: utf-8 -*-
"""
TKKアプリ系統表ビルド（算数・国語・自立活動）

  <board>.json          系統（枠組み）＋アプリの当てはめ
  _src/tkk_articles_full.json   tkk-fk.com の記事一覧・アプリ直リンク（スクレイプ結果）
  _template.html        ひな形
  → index.html / kokugo.html / jiritsu.html と、それぞれの日本語名コピー
"""
import base64, json, re, sys, urllib.parse
from pathlib import Path

HERE = Path(__file__).parent
arts = json.loads((HERE / "_src" / "tkk_articles_full.json").read_text(encoding="utf-8"))

# 表を足すときはここに1行足して <key>.json を置く
# nav だけのもの（よそのリポジトリにある表）は src を持たせず、href に絶対URLを書く
BOARDS = [
    {"key": "sansu",   "src": "keito.json",   "out": "index.html",   "label": "算数アプリ", "jp": "算数アプリ系統表.html"},
    {"key": "doga",    "label": "算数動画",   "href": "https://mararararai-mst.github.io/sansu-doga-eboard/"},
    {"key": "kokugo",  "src": "kokugo.json",  "out": "kokugo.html",  "label": "国語",       "jp": "国語アプリ系統表.html"},
    {"key": "jiritsu", "src": "jiritsu.json", "out": "jiritsu.html", "label": "自立活動",   "jp": "自立活動アプリ一覧.html"},
]
# 既定のnav＝この3枚だけ。公開ページにも、TKKさんに置いてもらう写しにも、これを使う。
# eboardの動画系統表を並べないのは、先方から「案内は学校内と家庭での学習の範囲に
# とどめてほしい」という条件をいただいているため（2026-10-06）。公開ページやよその
# サイトにボタンを置くと、不特定多数への案内になってしまう。
NAV = [{"label": b["label"], "href": b["out"]} for b in BOARDS if "src" in b]
# 校内配布用の日本語名コピーだけ、よそのリポジトリの表（eboard）も並べる。
# ファイルで校内の先生に渡すものなので、上の許可の範囲に収まる。
NAV_KONAI = [{"label": b["label"], "href": b.get("href") or b["out"]} for b in BOARDS]

# 同梱フォント(Zen Maru Gothic)に無い字は、形の近い字へ置き換える（1字だけ別フォントになるのを防ぐ）
FONT_SUB = {"―": "—"}  # ― → —


def clean_title(t):
    t = re.sub(r"^(?:【作成中】|作成中)?(?:【[^】]+】)+", "", t).strip()
    for a, b in FONT_SUB.items():
        t = t.replace(a, b)
    return t


def find(key):
    """keito.json の apps に書いたキーを、TKKの記事1件に解決する"""
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


def build(board, tpl):
    cfg = json.loads((HERE / board["src"]).read_text(encoding="utf-8"))
    apps, missing = {}, []

    def reg(key):
        if key in apps:
            return
        a = find(key)
        if a:
            apps[key] = a
        else:
            missing.append(key)

    for g in cfg["groups"]:
        for r in g["rows"]:
            for chips in r["cells"].values():
                for ch in chips:
                    for k in ch["apps"]:
                        reg(k)
    for it in cfg.get("tools", {}).get("items", []):
        for k in it["apps"]:
            reg(k)
    if missing:
        print(f"[{board['key']}] 未解決キー: {missing}", file=sys.stderr)
        sys.exit(1)

    data = {
        "grades": cfg["grades"],
        "groups": cfg["groups"],
        "tools": cfg.get("tools", {"name": "", "sub": "", "items": []}),
        "apps": apps,
        "boards": NAV,
        "self": board["out"],
        "colHead": cfg.get("colHead", "領域／系統"),
        "chainTitle": cfg.get("chainTitle", "この系統をたどる（上が下の学年）"),
        "beforeTitle": cfg.get("beforeTitle", "もっと前に戻るなら（別の系統）"),
        "nowLabel": cfg.get("nowLabel", "いま見ている学年"),
    }
    n_chips = sum(len(c) for g in cfg["groups"] for r in g["rows"] for c in r["cells"].values())

    html = tpl.replace("/*__DATA__*/", json.dumps(data, ensure_ascii=False))
    for k, v in cfg.get("text", {}).items():          # 先に表ごとの文言を入れる
        html = html.replace("__%s__" % k, v)
    html = html.replace("__NAPPS__", str(len(apps))).replace("__NCHIPS__", str(n_chips))
    assert "sansu-doga-eboard" not in html, "公開ページにeboardへのリンクが残っている"
    (HERE / board["out"]).write_text(html, encoding="utf-8")

    # ここから先は**フォントを埋め込んだ1枚もの**。
    # 学校のフィルタでURLが開けないときは、このファイルを渡せばネットを通らずに使える。
    # 検索エンジンには英語名の方を正とみなしてもらう（noindex）。
    noindex = '<meta name="robots" content="noindex">' + chr(10) + '<link rel="canonical"'
    emb = html.replace('<link rel="canonical"', noindex, 1)
    for w in ("Medium", "Bold"):
        f = HERE / "font" / ("ZenMaruGothic-%s.subset.woff2" % w)
        uri = "data:font/woff2;base64," + base64.b64encode(f.read_bytes()).decode()
        emb = emb.replace('url("font/ZenMaruGothic-%s.subset.woff2")' % w, 'url(%s)' % uri)
    assert "font/ZenMaruGothic" not in emb, "フォントの埋め込みに失敗"

    # 日本語名の配布用コピー＝校内の先生に渡すファイル。ここだけ nav に「算数動画」を足す。
    jp = emb.replace(json.dumps(NAV, ensure_ascii=False),
                     json.dumps(NAV_KONAI, ensure_ascii=False), 1)
    assert "sansu-doga-eboard" in jp, "校内配布版に算数動画のnavが入っていない"
    (HERE / board["jp"]).write_text(jp, encoding="utf-8")

    # TKKさんのサイトに置かせてもらう写し（keito/）。
    # 中身は上の1枚ものと同じだが、ファイル名を英語名にしてある＝3枚を行き来するリンクが
    # そのまま効く。フォルダごと置けば動く。検索は元のページに一本化したままにする
    # （noindex＋canonicalは元のURLのまま）。nav は3枚ぶんのまま＝写しの中で完結する。
    m = HERE / "keito"; m.mkdir(exist_ok=True)
    assert "sansu-doga-eboard" not in emb, "写しにeboardへのリンクが残っている"
    (m / board["out"]).write_text(emb, encoding="utf-8")
    print(f"OK {board['key']:8s} apps={len(apps):3d} chips={n_chips:3d} -> {board['out']} / {board['jp']} / keito/{board['out']}")


def main():
    tpl = (HERE / "_template.html").read_text(encoding="utf-8")
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for b in BOARDS:
        if only and b["key"] != only:
            continue
        if "src" not in b:          # nav だけの行（よそのリポジトリの表）
            continue
        if not (HERE / b["src"]).exists():
            print(f"-- {b['key']}: {b['src']} が無いので飛ばす")
            continue
        build(b, tpl)
    # 同梱フォントに無い字が増えていないか（文言を足したら _font.py で作り直す）
    import subprocess
    r = subprocess.run([sys.executable, str(HERE / "_font.py"), "--check"], capture_output=True,
                       text=True, encoding="utf-8", env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
    if r.returncode:
        print("!! 同梱フォントに無い字があります。python _font.py で作り直してください", file=sys.stderr)
        print(r.stdout, file=sys.stderr)


main()
