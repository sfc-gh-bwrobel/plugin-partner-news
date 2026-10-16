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


def render(md):
    out, para, in_list = [], [], False

    def flush():
        nonlocal para
        if para:
            out.append("<p>" + "<br>".join(para) + "</p>")
            para = []

    def close():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    for line in md.splitlines():
        h = re.match(r"^(#{1,3})\s+(.*)$", line)
        if h:
            flush(); close()
            n = len(h[1]) + 1  # digest h1 -> h2: the page owns h1
            out.append(f"<h{n}>{inline(h[2])}</h{n}>")
        elif re.match(r"^\s*-\s+", line):
            flush()
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append("<li>" + inline(re.sub(r"^\s*-\s+", "", line)) + "</li>")
        elif not line.strip():
            flush(); close()
        else:
            close()
            para.append(inline(line))
    flush(); close()
    return "\n".join(out)


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
    :root { color-scheme: light dark; }
    body {
      font-family: -apple-system, system-ui, "Segoe UI", sans-serif; line-height: 1.5;
      max-width: 880px; width: 100%; box-sizing: border-box;
      margin: 0 auto; padding: clamp(16px, 4vw, 24px);
      color: light-dark(#1f2937, #e5e7eb); background: light-dark(#ffffff, #0b1220);
    }
    h1, h2, h3, h4 { color: light-dark(#0f172a, #f1f5f9); line-height: 1.25; }
    h1 { font-size: 1.5rem; margin: 0.2em 0; }
    h2 { font-size: 1.35rem; margin: 0.6em 0 0.2em; }
    h3 { font-size: 1.15rem; margin-top: 1.6em; padding-bottom: 4px;
         border-bottom: 1px solid light-dark(#e5e7eb, #1f2937); }
    h4 { font-size: 1rem; margin-top: 1.2em; }
    a { color: light-dark(#0b6bcb, #60a5fa); overflow-wrap: anywhere; }
    code { font-size: 0.9em; background: light-dark(#f3f4f6, #1f2937); padding: 1px 4px; border-radius: 4px; }
    ul { padding-left: 1.2em; }
    .bar { display: flex; flex-wrap: wrap; gap: 8px 12px; align-items: center;
           padding: 10px 0; border-bottom: 1px solid light-dark(#e5e7eb, #1f2937); }
    .bar label { font-weight: 600; }
    select { font: inherit; padding: 4px 8px; border-radius: 6px; max-width: 100%;
             border: 1px solid light-dark(#d1d5db, #374151);
             background: light-dark(#fff, #111827); color: inherit; }
    .muted { color: light-dark(#6b7280, #9ca3af); font-size: 0.9rem; }
    section[hidden] { display: none; }
  </style>
</head>
<body>
  <h1>__TITLE__</h1>
  <div class="bar">
    <label for="week">Week</label>
    <select id="week">
__OPTIONS__
    </select>
    <span class="muted">__COUNT__ - built __BUILT__</span>
  </div>
__SECTIONS__
  <script>
    // Static page: all weeks are pre-rendered; this only shows the selected one.
    var weekEl = document.getElementById('week');
    function show(id) {
      document.querySelectorAll('section.digest').forEach(function (s) { s.hidden = s.id !== id; });
      window.scrollTo(0, 0);
    }
    weekEl.addEventListener('change', function () { show(weekEl.value); });
    show(weekEl.value);
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
        options.append(f'      <option value="{sid}"{sel}>Week ending {d}</option>')
        sections.append(f'  <section class="digest" id="{sid}">\n{render(f.read_text())}\n  </section>')

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
            .replace("__BUILT__", date.today().isoformat()))

    out = ROOT / "site" / f"{partner}-news.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(page)
    print(out, len(page), "bytes,", len(files), "weeks")


if __name__ == "__main__":
    main()
