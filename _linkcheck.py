# -*- coding: utf-8 -*-
"""TKKへのリンク切れチェック（定期実行）

公開中の3枚（index / kokugo / jiritsu）から tkk-fk.com のURLを全部抜き出し、
1本ずつ叩いて生死を見る。落ちていたら「どの単元のどのアプリか」まで添えて
Discordに通知する。

  python _linkcheck.py          通常（変化があったときだけ通知）
  python _linkcheck.py --force  結果にかかわらず通知
  python _linkcheck.py --quiet  通知せず標準出力だけ

TKKのサーバに負荷をかけないよう、1本ずつ0.4秒あけて叩く（約90秒）。
同時アクセスだと503が返ることが実測で分かっているため、並列にはしない。
落ちた分は10秒おいてもう一度だけ叩き、二度とも落ちたものだけを「切れ」と判定する。
"""
import json, re, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
BOARDS = [("index.html", "算数"), ("kokugo.html", "国語"), ("jiritsu.html", "自立活動")]
JSONS = [("keito.json", "算数"), ("kokugo.json", "国語"), ("jiritsu.json", "自立活動")]
STATE = HERE / "_linkcheck_state.json"
REPORT = HERE / "_linkcheck_report.txt"
UA = "Mozilla/5.0 (linkcheck; https://mararararai-mst.github.io/sansu-keito-tkk/)"
WAIT = 0.4


def where():
    """URL -> 「算数 / わり算 / 3年 / わり算の意味」の形に直す（複数箇所ならぜんぶ）"""
    arts = json.loads((HERE / "_src" / "tkk_articles_full.json").read_text(encoding="utf-8"))

    def urls_of(key):
        if key.startswith("t:"):
            hits = [a for a in arts if key[2:] in a["title"]]
        else:
            hits = [a for a in arts
                    if urllib.parse.unquote(a["url"]).rstrip("/").endswith("/" + key)]
        if len(hits) != 1:
            return []
        return [hits[0]["url"]] + list(hits[0]["apps"])

    m = {}
    for f, label in JSONS:
        if not (HERE / f).exists():
            continue
        cfg = json.loads((HERE / f).read_text(encoding="utf-8"))
        for g in cfg["groups"]:
            for r in g["rows"]:
                for grade, chips in r["cells"].items():
                    for ch in chips:
                        for k in ch["apps"]:
                            for u in urls_of(k):
                                m.setdefault(u, []).append(
                                    "%s / %s / %s / %s" % (label, r["name"], grade, ch["c"]))
        for it in cfg.get("tools", {}).get("items", []):
            for k in it["apps"]:
                for u in urls_of(k):
                    m.setdefault(u, []).append("%s / 先生の道具 / %s" % (label, it["g"]))
    return m


def collect():
    urls = set()
    for f, _ in BOARDS:
        p = HERE / f
        if p.exists():
            urls |= set(re.findall(r'https://tkk-fk\.com[^"\'\s<>]*', p.read_text(encoding="utf-8")))
    return sorted(urls)


def hit(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:
        return type(e).__name__


def main():
    force = "--force" in sys.argv
    quiet = "--quiet" in sys.argv
    urls = collect()
    if not urls:
        print("リンクが1本も取れなかった。ビルドされていない可能性がある", file=sys.stderr)
        sys.exit(2)

    res = {}
    for i, u in enumerate(urls, 1):
        res[u] = hit(u)
        print("  %3d/%d %s %s" % (i, len(urls), res[u], u))
        time.sleep(WAIT)

    bad = [u for u, s in res.items() if s != 200]
    if bad:                                   # 同時アクセス由来の一時エラーを除くため、間をあけて1回だけ再試行
        print("-- %d本が200以外。10秒おいて再確認" % len(bad))
        time.sleep(10)
        for u in bad:
            res[u] = hit(u)
            print("  再 %s %s" % (res[u], u))
            time.sleep(1.0)
        bad = [u for u in bad if res[u] != 200]

    loc = where()
    lines = ["TKKリンクチェック %s" % datetime.now().strftime("%Y-%m-%d %H:%M"),
             "  対象 %d本 / 切れ %d本" % (len(urls), len(bad)), ""]
    for u in bad:
        lines.append("  [%s] %s" % (res[u], u))
        for w in loc.get(u, ["（表のどこから張っているか特定できず）"]):
            lines.append("      %s" % w)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))

    prev = json.loads(STATE.read_text(encoding="utf-8"))["bad"] if STATE.exists() else []
    STATE.write_text(json.dumps({"at": datetime.now().isoformat(), "n": len(urls), "bad": bad},
                                ensure_ascii=False, indent=1), encoding="utf-8")
    changed = set(bad) != set(prev)
    if quiet or not (force or (bad and changed) or (prev and not bad)):
        return 1 if bad else 0

    sys.path.insert(0, str(Path.home() / "Documents" / "MSTbase" / "tools" / "文字起こしプロジェクト"))
    from notify import discord_notify
    if bad:
        head = "⚠️ TKK系統表 リンク切れ %d本 / %d本中" % (len(bad), len(urls))
        body = "\n".join(lines[2:])[:1600]
        discord_notify(head + "\n```\n" + body + "\n```", level="warn", target="monitor")
    else:
        discord_notify("✅ TKK系統表 リンク切れ解消（%d本すべて200）" % len(urls), target="monitor")
    return 1 if bad else 0


sys.exit(main())
