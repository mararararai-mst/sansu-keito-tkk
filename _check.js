// 実測チェック（フルチェック用）。ブラウザで: eval(await (await fetch('/_check.js')).text()); SWEEP('label')
// 対象は body * すべて（列挙しない）。overflow枠でクリップされた部分は除外、stickyヘッダ下の重なりは別扱い。
window.SWEEP = function (label) {
  if (document.documentElement.clientWidth < 200) throw new Error('pane hidden');
  const W = document.documentElement.clientWidth;
  const clipRect = e => {
    let r = e.getBoundingClientRect(); let box = { l: r.left, t: r.top, r: r.right, b: r.bottom };
    for (let p = e.parentElement; p && p !== document.body; p = p.parentElement) {
      const cs = getComputedStyle(p);
      if (cs.overflow !== 'visible' || cs.overflowX !== 'visible' || cs.overflowY !== 'visible') {
        const pr = p.getBoundingClientRect();
        box = { l: Math.max(box.l, pr.left), t: Math.max(box.t, pr.top), r: Math.min(box.r, pr.right), b: Math.min(box.b, pr.bottom) };
      }
    }
    return (box.r - box.l > 1 && box.b - box.t > 1) ? box : null;
  };
  const isSticky = e => { for (let p = e; p && p !== document.body; p = p.parentElement) if (getComputedStyle(p).position === 'sticky') return true; return false; };
  const vis = e => { const cs = getComputedStyle(e); return (cs.visibility !== 'hidden' && cs.display !== 'none' && e.offsetParent !== null) || cs.position === 'fixed'; };
  const all = [...document.querySelectorAll('body *')].filter(e => vis(e) && !['SCRIPT', 'STYLE'].includes(e.tagName));
  const res = { label, W, pageHScroll: document.documentElement.scrollWidth > W, hOverflow: [], vOverflow: [], orphan: [], textOverlap: [], stickyCover: 0, smallText: [] };
  const inScrollBox = e => { for (let p = e.parentElement; p; p = p.parentElement) { const o = getComputedStyle(p).overflowX; if (o === 'auto' || o === 'scroll') return true; } return false; };
  for (const e of all) {
    const r = e.getBoundingClientRect(); if (r.width === 0) continue;
    if (r.right > W + 1 && !inScrollBox(e) && getComputedStyle(e).position !== 'fixed') res.hOverflow.push(e.tagName + '.' + e.className + ':' + e.textContent.trim().slice(0, 20));
    const p = e.parentElement;
    if (p && p !== document.body) { const pr = p.getBoundingClientRect(); const cs = getComputedStyle(p); if (cs.overflow === 'visible' && cs.height !== 'auto' && r.bottom > pr.bottom + 1 && !inScrollBox(e)) res.vOverflow.push(e.tagName + '.' + e.className + ':' + e.textContent.trim().slice(0, 20)); }
    const fs = parseFloat(getComputedStyle(e).fontSize);
    if ([...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()) && fs < 11 && clipRect(e)) res.smallText.push(e.tagName + '.' + e.className + ' ' + fs + 'px:' + e.textContent.trim().slice(0, 15));
  }
  // 孤立折り返し：見出し・ボタン・短文（40字以下）は最終行3字未満で0件必須
  const cands = all.filter(e => ['BUTTON', 'H1', 'H2', 'H3', 'H4', 'TH', 'SPAN', 'A', 'LI', 'P', 'DIV'].includes(e.tagName) && getComputedStyle(e).display !== 'inline' && e.textContent.trim().length <= 40 && e.textContent.trim().length > 3 && clipRect(e));
  for (const e of cands) {
    const tn = [...e.childNodes].find(n => n.nodeType === 3 && n.textContent.trim()); if (!tn) continue;
    const range = document.createRange(); range.selectNodeContents(tn);
    const rects = [...range.getClientRects()].filter(r => r.width > 0); const lines = [];
    rects.forEach(r => { const L = lines.find(l => Math.min(l.b, r.bottom) - Math.max(l.t, r.top) > 0.35 * Math.min(l.b - l.t, r.height)); if (L) { L.l = Math.min(L.l, r.left); L.r = Math.max(L.r, r.right); L.t = Math.min(L.t, r.top); L.b = Math.max(L.b, r.bottom); } else lines.push({ l: r.left, r: r.right, t: r.top, b: r.bottom }); });
    if (lines.length < 2) continue; lines.sort((a, b) => a.t - b.t);
    const last = lines[lines.length - 1]; let lw = last.r - last.l;
    // 最終行にバッジ等のインライン要素が続いていれば、その幅も最終行に足す
    [...e.children].forEach(c => { const cr = c.getBoundingClientRect(); if (getComputedStyle(c).display.startsWith('inline') && Math.abs(cr.top - last.t) < cr.height) lw += cr.width + 6; });
    const fs = parseFloat(getComputedStyle(e).fontSize);
    if (lw < fs * 3 - 1) res.orphan.push(e.tagName + ':' + e.textContent.trim().slice(0, 30) + ' last=' + Math.round(lw / fs * 10) / 10 + '字');
  }
  // 文字どうしの重なり（クリップ後の矩形で）。stickyヘッダが覆うものは別カウント
  const leaves = all.filter(e => [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()));
  const rects = leaves.map(e => ({ e, r: clipRect(e) })).filter(x => x.r);
  for (let i = 0; i < rects.length; i++) for (let j = i + 1; j < rects.length; j++) {
    const A = rects[i], B = rects[j]; if (A.e.contains(B.e) || B.e.contains(A.e)) continue;
    const ix = Math.min(A.r.r, B.r.r) - Math.max(A.r.l, B.r.l), iy = Math.min(A.r.b, B.r.b) - Math.max(A.r.t, B.r.t);
    if (ix > 2 && iy > 2) { if (isSticky(A.e) !== isSticky(B.e)) res.stickyCover++; else res.textOverlap.push(A.e.textContent.trim().slice(0, 15) + ' × ' + B.e.textContent.trim().slice(0, 15)); }
  }
  res.counts = { hOverflow: res.hOverflow.length, vOverflow: res.vOverflow.length, orphan: res.orphan.length, textOverlap: res.textOverlap.length, smallText: res.smallText.length, stickyCover: res.stickyCover };
  for (const k of ['hOverflow', 'vOverflow', 'orphan', 'textOverlap', 'smallText']) res[k] = res[k].slice(0, 10);
  return res;
};
