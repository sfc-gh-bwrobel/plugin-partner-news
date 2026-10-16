#!/usr/bin/env python3
"""Build a static, self-contained digest page from digests/<partner>/digest-*.md (stdlib only).

Usage: python3 build_site.py capgemini   ->  site/<partner>-news.html
All weeks are pre-rendered into the HTML; the page needs no runtime loading or parsing.
"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def link(url, text):
    if re.match(r"https?://", url, re.I):
        return f'<a href="{url}" target="_blank" rel="noopener noreferrer">{text}</a>'
    return text


def inline(raw):
    s = html.escape(raw, quote=True)
    parts = []  # keep code spans and links out of later replacements

    def keep(h):
        parts.append(h)
        return f"\x00{len(parts) - 1}\x00"

    s = re.sub(r"`([^`]+)`", lambda m: keep(f"<code>{m[1]}</code>"), s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: keep(link(m[2], m[1])), s)
    s = re.sub(r"https?://[^\s<]+", lambda m: keep(link(m[0], m[0])), s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    return re.sub(r"\x00(\d+)\x00", lambda m: parts[int(m[1])], s)


SECTION_KINDS = [("snowflake", "snowflake"), ("subsidiar", "subsid"), ("top", "top"), ("people", "people"),
                 ("competitor", "compet"), ("coming", "coming"), ("also", "also"), ("manual", "manual")]
LABELS = {"why it matters": "why", "follow-up": "follow", "source": "source", "sources": "source"}


def slug(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")[:40]


def kind(title):
    t = title.lower()
    return next((k for key, k in SECTION_KINDS if key in t), "other")


def li(text):
    m = re.match(r"^([A-Za-z -]+):\s+(.*)$", text)
    if m and m[1].lower() in LABELS:
        return (f'<li class="lbl lbl-{LABELS[m[1].lower()]}"><span class="tag">{html.escape(m[1])}</span>'
                f'<span>{inline(m[2])}</span></li>')
    return f"<li>{inline(text)}</li>"


def render(md, sid):
    """Digest markdown -> week header, jump nav and section/story cards."""
    head, nav, body = [], [], []
    sec = story = None   # open section title / story flag
    count = 0            # stories or bullets in the open section
    buf = []             # html of the open section
    pre = True           # before the first ## section
    para, items, meta_next = [], [], False

    def flush_para():
        nonlocal para
        if para:
            target = head if pre else buf
            target.append("<p>" + "<br>".join(inline(x) for x in para) + "</p>")
            para = []

    def flush_list():
        nonlocal items
        if items:
            buf.append('<ul>' + "".join(li(x) for x in items) + "</ul>")
            items = []

    def close_story():
        nonlocal story
        flush_para(); flush_list()
        if story:
            buf.append("</article>")
            story = None

    def close_section():
        nonlocal sec, buf, count
        close_story()
        if sec is not None:
            k, sl = kind(sec), slug(sec)
            text = re.sub(r"<[^>]+>", "", "".join(buf)).strip()
            empty = text.lower().startswith("none")
            badge = "" if empty or not count else f'<span class="count">{count}</span>'
            body.append(f'<section class="card k-{k}{" empty" if empty else ""}" id="{sid}-{sl}">'
                        f'<h3><span class="dot"></span>{inline(sec)}{badge}</h3>{"".join(buf)}</section>')
            nav.append(f'<a class="chip k-{k}{" empty" if empty else ""}" href="#{sid}-{sl}">'
                       f'{html.escape(re.sub(r"[(].*", "", sec).strip())}</a>')
        sec, buf, count = None, [], 0

    for line in md.splitlines():
        h = re.match(r"^(#{1,3})\s+(.*)$", line)
        if h and len(h[1]) == 1:
            head.append(f"<h2>{inline(h[2])}</h2>")
        elif h and len(h[1]) == 2:
            flush_para(); close_section(); pre = False
            sec = h[2]
        elif h:
            close_story()
            num = re.match(r"^(\d+)\.\s+(.*)$", h[2])
            n, title = (num[1], num[2]) if num else ("", h[2])
            buf.append(f'<article class="story">{f"<span class=num>{n}</span>" if n else ""}'
                       f"<h4>{inline(title)}</h4>")
            story, meta_next = True, True
            count += 1
        elif re.match(r"^\s*-\s+", line):
            flush_para()
            items.append(re.sub(r"^\s*-\s+", "", line))
            if not story:
                count += 1
        elif not line.strip():
            flush_para(); flush_list()
        elif pre and "|" in line and ":" in line:
            chips = "".join(f'<span class="stat">{inline(c.strip())}</span>' for c in line.split("|"))
            head.append(f'<div class="stats">{chips}</div>')
        elif pre:
            head.append(f'<p class="note">{inline(line)}</p>')
        elif meta_next:
            flush_list()
            buf.append(f'<p class="meta">{inline(line)}</p>')
            meta_next = False
        else:
            flush_list()
            para.append(line)
        if line.strip() and not (h and len(h[1]) == 3):
            meta_next = False
    close_section()
    return ('<header class="week">' + "".join(head) + '<nav class="jump">' + "".join(nav) + "</nav></header>"
            + "".join(body))


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="snowflake-source" content="cortex-agent-authored" />
  <base target="_top" />
  <title>__TITLE__</title>
  <script type="application/json" id="snowflake-report-metadata">
__META__
  </script>
  <style>
    :root {
      color-scheme: light dark;
      --bg: light-dark(#f4f6fa, #0b1220); --card: light-dark(#ffffff, #121b2e);
      --ink: light-dark(#1f2937, #e5e7eb); --head: light-dark(#0f172a, #f8fafc);
      --muted: light-dark(#64748b, #94a3b8); --line: light-dark(#e2e8f0, #1e293b);
      --link: light-dark(#0b6bcb, #7cc4ff); --accent: #29b5e8;
      --shadow: 0 1px 2px rgb(15 23 42 / .06), 0 4px 16px rgb(15 23 42 / .05);
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; scroll-padding-top: 84px; }
    body { margin: 0; background: var(--bg); color: var(--ink);
           font: 16px/1.6 -apple-system, system-ui, "Segoe UI", Roboto, sans-serif; }
    a { color: var(--link); text-decoration-thickness: 1px; text-underline-offset: 2px; overflow-wrap: anywhere; }
    a:focus-visible, button:focus-visible, select:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
    code { font-size: .85em; background: light-dark(#eef2f7, #1e293b); padding: 1px 5px; border-radius: 4px; }
    .top { position: sticky; top: 0; z-index: 10; backdrop-filter: blur(10px);
           background: light-dark(rgb(255 255 255 / .85), rgb(11 18 32 / .85)); border-bottom: 1px solid var(--line); }
    .top-in, main { max-width: 1280px; margin: 0 auto; padding: 0 clamp(14px, 4vw, 24px); }
    .top-in { display: flex; flex-wrap: wrap; align-items: center; gap: 10px 16px; padding-block: 12px; }
    .brand { display: flex; align-items: center; gap: 10px; margin-right: auto; }
    .logo { width: 32px; height: 32px; border-radius: 8px; display: grid; place-items: center;
            background: linear-gradient(135deg, #29b5e8, #0070c0); color: #fff; font-weight: 700; }
    h1 { font-size: 1.1rem; margin: 0; color: var(--head); letter-spacing: -.01em; }
    .sub { font-size: .8rem; color: var(--muted); }
    .picker { display: flex; align-items: center; gap: 6px; }
    select, button { font: inherit; font-size: .9rem; color: inherit; background: var(--card);
                     border: 1px solid var(--line); border-radius: 8px; padding: 6px 10px; min-height: 36px; }
    button { cursor: pointer; width: 36px; padding: 0; }
    button:disabled { opacity: .35; cursor: default; }
    main { padding-block: 24px 64px; }
    .week h2 { font-size: clamp(1.4rem, 3.5vw, 1.9rem); line-height: 1.2; margin: 4px 0 12px;
               color: var(--head); letter-spacing: -.02em; }
    .stats { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 10px; }
    .stat { font-size: .8rem; background: var(--card); border: 1px solid var(--line); border-radius: 999px; padding: 3px 10px; }
    .stat:first-child { background: light-dark(#fff7e6, #3a2a06); border-color: light-dark(#f5c26b, #7a5a12); font-weight: 600; }
    .note { font-size: .85rem; color: var(--muted); margin: 0 0 16px; }
    .jump { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 24px; }
    .chip { font-size: .8rem; text-decoration: none; color: var(--ink); background: var(--card);
            border: 1px solid var(--line); border-left: 3px solid var(--k); border-radius: 6px; padding: 3px 10px; }
    .chip:hover { border-color: var(--k); }
    .chip.empty { color: var(--muted); }
    .card { background: var(--card); border: 1px solid var(--line); border-top: 3px solid var(--k);
            border-radius: 12px; padding: 18px clamp(16px, 3vw, 24px); margin-bottom: 18px; box-shadow: var(--shadow); }
    .card h3 { display: flex; align-items: center; gap: 10px; font-size: 1.05rem; margin: 0 0 8px; color: var(--head); }
    .dot { width: 10px; height: 10px; border-radius: 50%; background: var(--k); flex: none; }
    .count { margin-left: auto; font-size: .75rem; font-weight: 600; color: var(--k);
             background: color-mix(in srgb, var(--k) 14%, transparent); border-radius: 999px; padding: 1px 9px; }
    .card.empty { box-shadow: none; background: transparent; border-style: dashed; border-top-style: solid; padding-block: 12px; }
    .card.empty p { color: var(--muted); margin: 0; font-size: .9rem; }
    .card.k-snowflake:not(.empty) { background: linear-gradient(180deg, color-mix(in srgb, var(--k) 9%, var(--card)), var(--card) 70%); }
    .k-snowflake { --k: #29b5e8; } .k-subsid { --k: #8b5cf6; } .k-top { --k: #0f62fe; } .k-people { --k: #10b981; }
    .k-compet { --k: #f97316; } .k-coming { --k: #eab308; } .k-also { --k: #94a3b8; } .k-manual { --k: #64748b; } .k-other { --k: #94a3b8; }
    .story { position: relative; padding: 16px 0 6px 44px; border-top: 1px solid var(--line); }
    .story:first-of-type { border-top: 0; padding-top: 6px; }
    .num { position: absolute; left: 0; top: 16px; width: 30px; height: 30px; border-radius: 50%;
           display: grid; place-items: center; font-size: .85rem; font-weight: 700;
           color: var(--k); background: color-mix(in srgb, var(--k) 12%, transparent); }
    .story:first-of-type .num { top: 6px; }
    .story h4 { font-size: 1.02rem; line-height: 1.35; margin: 2px 0 4px; color: var(--head); }
    .meta { font-size: .78rem; color: var(--muted); margin: 0 0 6px; text-transform: none; }
    .story p { margin: 0 0 8px; }
    ul { padding-left: 1.1em; margin: 6px 0; }
    li { margin: 4px 0; }
    li.lbl { list-style: none; margin-left: -1.1em; display: grid; grid-template-columns: 128px 1fr; gap: 12px; font-size: .92rem; }
    .tag { font-size: .7rem; font-weight: 700; text-transform: uppercase; letter-spacing: .04em;
           align-self: start; padding: 2px 8px; white-space: nowrap; border-radius: 4px; text-align: center; margin-top: 2px; }
    .lbl-why .tag { color: #0f62fe; background: color-mix(in srgb, #0f62fe 12%, transparent); }
    .lbl-follow .tag { color: #059669; background: color-mix(in srgb, #10b981 14%, transparent); }
    .lbl-source .tag { color: var(--muted); background: color-mix(in srgb, #94a3b8 16%, transparent); }
    .lbl-source { font-size: .85rem; }
    @media (max-width: 560px) { li.lbl { grid-template-columns: 1fr; gap: 2px; } .tag { justify-self: start; } .story { padding-left: 0; } .num { position: static; display: inline-grid; margin-bottom: 4px; } }
    @media (min-width: 1100px) {
      .card.k-top:not(.empty) { display: grid; grid-template-columns: 1fr 1fr; gap: 0 32px; }
      .card.k-top h3 { grid-column: 1 / -1; }
      .card.k-top .story { border-top: 1px solid var(--line); padding-top: 16px; }
      .card.k-top .story .num { top: 16px; }
      .card.k-top .story:nth-of-type(-n+2) { border-top: 0; padding-top: 6px; }
      .card.k-top .story:nth-of-type(-n+2) .num { top: 6px; }
    }
    section.digest[hidden] { display: none; }
    footer { text-align: center; font-size: .8rem; color: var(--muted); padding-bottom: 32px; }
  </style>
</head>
<body>
  <div class="top"><div class="top-in">
    <div class="brand"><div class="logo" aria-hidden="true">__INITIAL__</div>
      <div><h1>__TITLE__</h1><div class="sub">Weekly partner intel for the Snowflake team - __COUNT__</div></div></div>
    <div class="picker">
      <button id="prev" aria-label="Previous (older) week" title="Older week">&#8249;</button>
      <label class="sub" for="week" style="position:absolute;left:-9999px">Week</label>
      <select id="week">
__OPTIONS__
      </select>
      <button id="next" aria-label="Next (newer) week" title="Newer week">&#8250;</button>
    </div>
  </div></div>
  <main>
__SECTIONS__
  </main>
  <footer>Built __BUILT__ from public sources. Suggestions are not facts - check the linked articles.</footer>
  <script>
    // Static page: all weeks are pre-rendered; this only shows the selected one.
    var weekEl = document.getElementById('week'), prev = document.getElementById('prev'), next = document.getElementById('next');
    function show() {
      document.querySelectorAll('section.digest').forEach(function (s) { s.hidden = s.id !== weekEl.value; });
      next.disabled = weekEl.selectedIndex === 0;
      prev.disabled = weekEl.selectedIndex === weekEl.options.length - 1;
      window.scrollTo(0, 0);
    }
    function step(d) { weekEl.selectedIndex += d; show(); }
    // In-page jumps: <base target="_top"> would navigate the Apps Script wrapper instead.
    document.addEventListener('click', function (e) {
      var a = e.target.closest('a.chip');
      if (!a) return;
      e.preventDefault();
      var t = document.getElementById(a.getAttribute('href').slice(1));
      if (t) t.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
    weekEl.addEventListener('change', show);
    prev.addEventListener('click', function () { step(1); });
    next.addEventListener('click', function () { step(-1); });
    show();
  </script>
</body>
</html>
"""


def main():
    partner = sys.argv[1] if len(sys.argv) > 1 else "capgemini"
    cfg = json.loads((ROOT / "partners" / f"{partner}.json").read_text())
    files = sorted((ROOT / "digests" / partner).glob("digest-*.md"), reverse=True)
    if not files:
        sys.exit(f"no digests in digests/{partner}/")

    options, sections = [], []
    for i, f in enumerate(files):
        d = re.search(r"(\d{4}-\d{2}-\d{2})", f.name)[1]
        sid = f"w{d}"
        sel = " selected" if i == 0 else ""
        options.append(f'      <option value="{sid}"{sel}>Week ending {d}{' (latest)' if i == 0 else ''}</option>')
        sections.append(f'  <section class="digest" id="{sid}">\n{render(f.read_text(), sid)}\n  </section>')

    title = f"{cfg['name']} news digest"
    meta = json.dumps({
        "generated": date.today().isoformat(),
        "intent": "Static weekly partner news digest page",
        "dataSources": [{"type": "file", "path": f"digests/{partner}/digest-*.md"}],
        "sections": [{"id": f"w{re.search(r'(\d{4}-\d{2}-\d{2})', f.name)[1]}", "title": f.name} for f in files],
        "producerNotes": f"Rebuild with: python3 build_site.py {partner}",
    }, indent=2)
    page = (PAGE.replace("__TITLE__", html.escape(title)).replace("__META__", meta)
            .replace("__OPTIONS__", "\n".join(options)).replace("__SECTIONS__", "\n".join(sections))
            .replace("__COUNT__", f"{len(files)} week{'s' if len(files) != 1 else ''}")
            .replace("__INITIAL__", html.escape(cfg["name"][:1])).replace("__BUILT__", date.today().isoformat()))

    out = ROOT / "site" / f"{partner}-news.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(page)
    print(out, len(page), "bytes,", len(files), "weeks")


if __name__ == "__main__":
    main()
