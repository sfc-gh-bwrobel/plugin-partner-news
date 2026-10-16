#!/usr/bin/env python3
"""Build a self-contained digest page from digests/<partner>/digest-*.md.

Usage: python3 build_site.py capgemini -> site/<partner>-news.html
All weeks are pre-rendered; the page needs no runtime loading or parsing.
"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parent


def link(url, text):
    if re.match(r"https?://", url, re.I):
        return f'<a href="{url}" target="_blank" rel="noopener noreferrer">{text}</a>'
    return text


def inline(raw):
    text = html.escape(raw, quote=True)
    parts = []

    def keep(markup):
        parts.append(markup)
        return f"\x00{len(parts) - 1}\x00"

    text = re.sub(r"`([^`]+)`", lambda match: keep(f"<code>{match[1]}</code>"), text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda match: keep(link(match[2], match[1])), text)
    text = re.sub(r"https?://[^\s<]+", lambda match: keep(link(match[0], match[0])), text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    return re.sub(r"\x00(\d+)\x00", lambda match: parts[int(match[1])], text)


SECTION_KINDS = [("snowflake", "snowflake"), ("subsidiar", "subsid"), ("top", "top"),
                 ("client stor", "clients"), ("people", "people"), ("competitor", "compet"),
                 ("coming", "coming"), ("more news", "more"), ("also", "also"), ("manual", "manual")]


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40]


def kind(title):
    return next((value for key, value in SECTION_KINDS if key in title.lower()), "other")


def blocks(lines):
    """Render the digest's paragraph/list subset, escaping all source text."""
    output, paragraph, items = [], [], []

    def flush():
        if paragraph:
            output.append('<p>' + '<br>'.join(inline(line) for line in paragraph) + '</p>')
            paragraph.clear()
        if items:
            output.append('<ul>' + ''.join(f'<li>{inline(item)}</li>' for item in items) + '</ul>')
            items.clear()

    for line in lines:
        if not line.strip():
            flush()
        elif re.match(r'^\s*-\s+', line):
            if paragraph:
                flush()
            items.append(re.sub(r'^\s*-\s+', '', line))
        else:
            if items:
                flush()
            paragraph.append(line)
    flush()
    return '\n'.join(output)


def parse_digest(markdown):
    title, metadata, sections = '', [], []
    section = None
    for line in markdown.splitlines():
        if line.startswith('# '):
            title = line[2:]
        elif line.startswith('## '):
            section = {'title': line[3:], 'lines': [], 'stories': []}
            sections.append(section)
        elif section is None:
            if line.strip():
                metadata.append(line)
        else:
            heading = re.match(r'^###\s+(?:\d+\.\s+)?(.*)$', line)
            if heading:
                section['stories'].append({'title': heading[1], 'lines': []})
            elif section['stories']:
                section['stories'][-1]['lines'].append(line)
            else:
                section['lines'].append(line)
    return title, metadata, sections


def story_html(story, client=False):
    title = re.sub(r'^Client stor(?:y|ies):\s*', '', story['title'], flags=re.I) if client else story['title']
    lines = list(story['lines'])
    while lines and not lines[0].strip():
        lines.pop(0)
    meta = ''
    if lines and '|' in lines[0]:
        meta = f'<p class="meta">{inline(lines.pop(0))}</p>'
    body, sources, suggestions = [], [], []
    for line in lines:
        match = re.match(r'^\s*-\s+(Why it matters|Follow-up|Sources?):\s+(.*)$', line, re.I)
        if match and match[1].lower().startswith('source'):
            sources.append(inline(match[2]))
        elif match:
            suggestions.append(f'<p><strong>{html.escape(match[1])}:</strong> {inline(match[2])}</p>')
        else:
            body.append(line)
    source_html = '<p class="sources"><span>Source: </span>' + '; '.join(sources) + '</p>' if sources else ''
    angle = ('<details class="angle"><summary>Team take <span>Suggested</span></summary>'
             '<div class="angle-body"><p class="annotation">Interpretation and possible follow-up, not reported facts.</p>'
             + ''.join(suggestions) + '</div></details>') if suggestions else ''
    return (f'<article class="story"><h4>{inline(title)}</h4>{meta}\n'
            + blocks(body) + '\n' + source_html + angle + '</article>')


def more_news_html(sections, sid):
    """Render curated topic bullets; date prefixes make ordering deterministic."""
    groups = {}
    for section in sections:
        candidates = ([{'title': 'Other news', 'lines': section['lines']}]
                      + section['stories'])
        for group in candidates:
            items = [re.sub(r'^\s*-\s+', '', line) for line in group['lines']
                     if re.match(r'^\s*-\s+', line)]
            if items:
                groups.setdefault(group['title'], []).extend(items)
    if not groups:
        return ''
    entries = [(topic, item) for topic, items in groups.items() for item in items]
    entries.sort(key=lambda entry: entry[1][:10] if re.match(r'^\d{4}-\d{2}-\d{2}\s*\|', entry[1]) else '',
                 reverse=True)

    entries_preview = entries[:12]

    def grouped_html(entries, continued=False):
        output = []
        for topic in groups:
            items = [item for name, item in entries if name == topic]
            if items:
                suffix = ' (continued)' if continued and any(name == topic for name, _ in entries_preview) else ''
                output.append('<div class="news-topic"><h4>' + inline(topic + suffix)
                              + '</h4>' + blocks(['- ' + item for item in items]) + '</div>')
        return '<div class="more-news-grid">' + ''.join(output) + '</div>'

    output = grouped_html(entries[:12])
    if len(entries) > 12:
        output += ('<details class="remaining-news"><summary>Show remaining news ('
                   + str(len(entries) - 12) + ')</summary>'
                   + grouped_html(entries[12:], continued=True) + '</details>')
    return (f'<section class="more-news" id="{sid}-more" aria-labelledby="{sid}-more-title">'
            f'<h3 id="{sid}-more-title">More news</h3>' + output + '</section>')


def render(markdown, sid):
    """Editorial hierarchy: news, client stories, short briefs, then provenance."""
    title, metadata, sections = parse_digest(markdown)
    news, clients, briefs, empty, checks, more = [], [], [], [], [], []
    for section in sections:
        category = kind(section['title'])
        plain = '\n'.join(section['lines']).strip()
        if category == 'manual':
            checks.append(section)
        elif not section['stories'] and (not plain or re.match(r'^None\b', plain, re.I)):
            empty.append(section)
        elif category in ('more', 'also'):
            more.append(section)
        elif category in ('top', 'clients'):
            if plain:
                (clients if category == 'clients' else news).append(blocks(section['lines']))
            for story in section['stories']:
                is_client = category == 'clients' or bool(re.match(r'^Client stor(?:y|ies):', story['title'], re.I))
                (clients if is_client else news).append(story_html(story, client=is_client))
        else:
            briefs.append(section)

    display_title = re.sub(r'^.*?\s+-\s+week of\s+', 'Week of ', title, flags=re.I)
    nav = []
    content = []
    if news:
        nav.append(f'<a href="#{sid}-news">News</a>')
        content.append(f'<section class="news" id="{sid}-news" aria-labelledby="{sid}-news-title">'
                       f'<h3 id="{sid}-news-title">The news</h3>' + '\n'.join(news) + '</section>')
    if clients:
        nav.append(f'<a href="#{sid}-clients">Client stories</a>')
        content.append(f'<section class="clients" id="{sid}-clients" aria-labelledby="{sid}-clients-title">'
                       f'<div class="section-heading"><h3 id="{sid}-clients-title">Client stories</h3>'
                       '<p>Delivery examples from the field</p></div><div class="client-grid">'
                       + '\n'.join(clients) + '</div></section>')
    more_html = more_news_html(more, sid)
    if more_html:
        nav.append(f'<a href="#{sid}-more">More news</a>')
        content.append(more_html)
    if briefs:
        nav.append(f'<a href="#{sid}-briefs">In brief</a>')
        brief_html = []
        # Upcoming dates stay easy to find; relative order of other categories is preserved.
        for index, section in sorted(enumerate(briefs), key=lambda item: kind(item[1]['title']) != 'coming'):
            brief_html.append(f'<section class="brief" id="{sid}-brief-{index}">'
                              f'<h4>{inline(section["title"])}</h4>' + blocks(section['lines'])
                              + ''.join(story_html(story) for story in section['stories']) + '</section>')
        content.append(f'<aside class="briefs" id="{sid}-briefs" aria-labelledby="{sid}-briefs-title">'
                       f'<h3 id="{sid}-briefs-title">In brief</h3>' + '\n'.join(brief_html) + '</aside>')
    coverage = ''
    if empty:
        names = [html.escape(re.sub(r'\s*\(.*', '', section['title'])) for section in empty]
        coverage = '<p class="coverage"><strong>No updates found:</strong> ' + ' &middot; '.join(names) + '.</p>'
    edition_notes = [line.removeprefix('Edition note:').strip() for line in metadata
                     if line.startswith('Edition note:')]
    edition_note_html = ''.join(f'<p class="edition-note">{inline(note)}</p>' for note in edition_notes)
    provenance = blocks(metadata)
    if empty:
        provenance += '<h4>Coverage notes</h4>' + ''.join(
            f'<p><strong>{inline(section["title"])}:</strong> {inline(" ".join(section["lines"]).strip())}</p>'
            for section in empty)
    for section in checks:
        provenance += f'<h4>{inline(section["title"])}</h4>' + blocks(section['lines'])
    return (f'<header class="week"><div class="eyebrow">Weekly briefing</div>'
            f'<h2>{inline(display_title)}</h2><nav class="jump" aria-label="Sections in this week">'
            + ''.join(nav) + '</nav>' + edition_note_html + coverage + '</header>\n'
            + '<div class="edition-grid">' + '\n'.join(content) + '</div>\n'
            + '<details class="about"><summary>About this digest &amp; source coverage</summary>'
            + '<div class="about-body"><p>Compiled from public sources. Team takes are editorial suggestions, '
            'not reported facts. Check the linked articles before acting.</p>' + provenance + '</div></details>')


def source_directory(cfg):
    """Describe current collector configuration, not historical run success."""
    feeds = cfg.get('feeds', [])
    google = cfg.get('google_news', {})
    queries, locales = google.get('queries', []), google.get('locales', [])
    content = ['<p>Current monitoring configuration. This is not a record of successful checks for each archived week. '
               'Google News searches across publishers; the articles cited above are the sources used in that edition.</p>']
    if feeds:
        content.append('<h3>Automated RSS feeds</h3><ul>' + ''.join(
            f'<li>{link(html.escape(feed["url"], quote=True), html.escape(feed["id"]))}'
            f'<br><span>{html.escape(feed["url"])}</span></li>' for feed in feeds) + '</ul>')
    if queries and locales:
        content.append('<h3>Google News searches</h3><p>Each query runs in every edition listed below. '
                       'Links open the query in Google News; the collector adds the scan date window.</p><ul>')
        for query in queries:
            editions = []
            for locale in locales:
                url = 'https://news.google.com/search?' + urlencode({'q': query['q'], **locale})
                label = f'{locale["hl"]} / {locale["gl"]}'
                editions.append(link(html.escape(url, quote=True), html.escape(label)))
            content.append(f'<li><strong>{html.escape(query["section"].capitalize())}</strong>'
                           f'<br><code>{html.escape(query["q"])}</code><br>' + ' &middot; '.join(editions) + '</li>')
        content.append('</ul>')
    if cfg.get('manual_checks'):
        content.append('<h3>Manual checks, not automated</h3><p>Listed for human review; inclusion does not mean a check was completed.</p>'
                       + blocks(['- ' + item for item in cfg['manual_checks']]))
    return ('<details class="about source-directory" id="monitored-sources">'
            f'<summary>Sources we search <span>({len(feeds)} RSS feeds, {len(queries) * len(locales)} news searches)</span></summary>'
            '<div class="about-body">' + ''.join(content) + '</div></details>')


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="snowflake-source" content="cortex-agent-authored" />
  <title>__TITLE__</title>
  <script type="application/json" id="snowflake-report-metadata">
__META__
  </script>
  <style>
    :root {
      color-scheme: light dark;
      --bg: light-dark(#fafaf8, #10151c); --paper: light-dark(#ffffff, #17202a);
      --ink: light-dark(#303843, #dbe2ea); --head: light-dark(#142330, #f1f5f9);
      --muted: light-dark(#596675, #a1adbc); --line: light-dark(#dce1e5, #344150);
      --soft: light-dark(#eef2f4, #202d3b); --link: light-dark(#075e91, #8bd2fb);
    }
    * { box-sizing: border-box; }
    body { margin: 0; background: var(--bg); color: var(--ink);
      font: 16px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    h1, h2, h3, h4 { color: var(--head); }
    h1 { margin: 0; font-size: 1.05rem; letter-spacing: -.025em; }
    h2 { margin: 8px 0 18px; font-size: clamp(1.65rem, 3vw, 2.6rem); line-height: 1.18; letter-spacing: -.04em; }
    h3 { margin: 0 0 20px; font-size: 1.05rem; letter-spacing: -.01em; }
    h4 { margin: 0 0 8px; font-size: 1.14rem; line-height: 1.35; letter-spacing: -.015em; }
    p { margin: 0 0 12px; }
    a { color: var(--link); text-underline-offset: 3px; overflow-wrap: anywhere; }
    a:hover { text-decoration-thickness: 2px; }
    a:focus-visible, button:focus-visible, select:focus-visible, summary:focus-visible {
      outline: 3px solid var(--link); outline-offset: 4px; border-radius: 3px; }
    .top { background: var(--paper); border-bottom: 1px solid var(--line); }
    .top-in, main, footer { width: 100%; max-width: 1440px; margin: 0 auto; padding-inline: clamp(18px, 3vw, 48px); }
    .top-in { display: flex; align-items: center; flex-wrap: wrap; gap: 12px 24px; padding-block: 16px; }
    .brand { margin-right: auto; }
    .sub { font-size: .78rem; color: var(--muted); }
    .picker { display: flex; align-items: center; gap: 6px; max-width: 100%; }
    select, button { color: var(--ink); background: var(--paper); border: 1px solid var(--line);
      border-radius: 6px; min-height: 44px; font: inherit; font-size: .84rem; }
    select { padding: 8px; min-width: 0; max-width: 100%; }
    button { flex: 0 0 44px; cursor: pointer; font-size: 1.3rem; }
    button:disabled { opacity: .4; cursor: default; }
    .sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden;
      clip: rect(0,0,0,0); white-space: nowrap; border: 0; }
    .skip { position: absolute; left: 18px; top: -100px; padding: 8px 16px; background: var(--paper); z-index: 10; }
    .skip:focus { top: 8px; }
    main { padding-block: 32px 48px; }
    .eyebrow { display: flex; align-items: center; gap: 12px; font-size: .73rem; font-weight: 650;
      letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
    .status { text-transform: none; letter-spacing: 0; font-weight: 500; border-left: 1px solid var(--line); padding-left: 12px; }
    .jump { display: flex; gap: 8px 28px; flex-wrap: wrap; border-bottom: 1px solid var(--line); }
    .jump a { display: inline-flex; align-items: center; min-height: 44px; color: var(--ink); font-size: .9rem; text-decoration: none; }
    .jump a:hover { color: var(--link); text-decoration: underline; }
    .coverage { color: var(--muted); font-size: .8rem; margin: 10px 0 0; }
    .coverage strong { font-weight: 500; }
    .edition-grid { display: grid; grid-template-columns: minmax(0, 2.1fr) minmax(0, 1fr);
      grid-template-areas: "news briefs" "clients clients" "more more"; gap: 40px 48px; margin-top: 30px; align-items: start; }
    .news { grid-area: news; min-width: 0; }
    .story { min-width: 0; padding-block: 22px; border-top: 1px solid var(--line); }
    .news > .story:first-of-type { border-top: 0; padding-top: 0; }
    .news > .story:first-of-type h4 { font-size: clamp(1.25rem, 2vw, 1.65rem); }
    .news .story > p { max-width: 76ch; }
    .meta { font-size: .76rem; color: var(--muted); }
    .sources { font-size: .8rem; margin-top: 12px; }
    .sources > span { color: var(--muted); }
    summary { cursor: pointer; }
    .angle { font-size: .86rem; }
    .angle > summary { display: list-item; width: fit-content; padding-block: 8px; color: var(--link); }
    .angle > summary > span { font-size: .72rem; color: var(--muted); margin-left: 6px; }
    .angle-body { border-left: 2px solid var(--line); padding: 8px 16px; margin: 4px 0 0; }
    .angle-body p:last-child { margin-bottom: 0; }
    .annotation { font-size: .76rem; color: var(--muted); }
    .clients { grid-area: clients; min-width: 0; border-top: 2px solid var(--head); padding-top: 22px; }
    .section-heading { display: flex; align-items: baseline; flex-wrap: wrap; gap: 4px 20px; margin-bottom: 18px; }
    .section-heading h3 { margin: 0; }
    .section-heading p { margin: 0; font-size: .84rem; color: var(--muted); }
    .client-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 24px; }
    .client-grid > .story { background: var(--paper); border: 1px solid var(--line); border-radius: 8px; padding: 22px; }
    .more-news { grid-area: more; min-width: 0; border-top: 1px solid var(--line); padding-top: 22px; }
    .more-news-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 24px 48px; }
    .news-topic { min-width: 0; }
    .news-topic h4 { font-size: .9rem; }
    .news-topic li { font-size: .9rem; overflow-wrap: anywhere; }
    .remaining-news { margin-top: 20px; }
    .remaining-news > summary { padding-block: 12px; font-size: .87rem; color: var(--link); }
    .remaining-news > .more-news-grid { margin-top: 16px; }
    .briefs { grid-area: briefs; min-width: 0; background: var(--soft); border-radius: 8px; padding: 24px; }
    .briefs h3 { font-size: .76rem; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
    .brief { border-top: 1px solid var(--line); padding-top: 18px; margin-top: 18px; font-size: .87rem; }
    .brief:first-of-type { border-top: 0; padding-top: 0; margin-top: 0; }
    .brief h4 { font-size: .96rem; }
    ul { margin: 0; padding-left: 18px; }
    li { margin-block: 10px; }
    .brief li:last-child { margin-bottom: 0; }
    .about { border-top: 1px solid var(--line); margin-top: 36px; font-size: .82rem; color: var(--muted); }
    .about > summary { padding-block: 16px; }
    .about-body { max-width: 90ch; padding-bottom: 16px; }
    .about h4 { font-size: .87rem; margin-top: 18px; }
    .source-directory { margin-top: 0; }
    .source-directory h3 { font-size: .9rem; margin: 20px 0 8px; }
    .source-directory li { overflow-wrap: anywhere; }
    .source-directory summary span { font-size: .76rem; }
    code { overflow-wrap: anywhere; font-size: .88em; }
    .history { padding-block: 24px; }
    .history h3 { margin-bottom: 8px; }
    .history h4 { margin-top: 24px; }
    .history-link { font-size: .85rem; padding-block: 12px; }
    .edition-download { font-size: .82rem; margin-block: 16px; }
    footer { border-top: 1px solid var(--line); padding-block: 20px 32px; font-size: .76rem; color: var(--muted); }
    [hidden] { display: none !important; }
    section[id], aside[id] { scroll-margin-top: 24px; }
    @media (max-width: 1000px) {
      .edition-grid { gap: 32px 24px; grid-template-columns: minmax(0, 1.6fr) minmax(0, 1fr); }
      .client-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .briefs { padding: 20px; }
    }
    @media (max-width: 720px) {
      .edition-grid { grid-template-columns: minmax(0, 1fr); grid-template-areas: "news" "clients" "more" "briefs"; }
      .client-grid, .more-news-grid { grid-template-columns: minmax(0, 1fr); }
      .picker { width: 100%; }
      select { flex: 1 1 auto; }
      main { padding-top: 24px; }
    }
    @media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }
  </style>
</head>
<body>
  <a class="skip" href="#content">Skip to digest</a>
  <header class="top"><div class="top-in">
    <div class="brand"><h1>__TITLE__</h1><div class="sub">Public-source intelligence for the Snowflake partner team</div></div>
    __HISTORY_NAV__
    <div class="picker">
      <button id="prev" aria-label="Previous (older) week" title="Older week">&#8249;</button>
      <label class="sr-only" for="week">Week</label>
      <select id="week">
__OPTIONS__
      </select>
      <button id="next" aria-label="Next (newer) week" title="Newer week">&#8250;</button>
    </div>
  </div></header>
  <main id="content" tabindex="-1">
__SECTIONS__
__SOURCE_DIRECTORY__
__HISTORY__
  </main>
  <footer>Created and maintained by Bart Wrobel.<br>Built __BUILT__ &middot; Public sources &middot; __COUNT__</footer>
  <script>
    const weekEl = document.getElementById('week');
    const older = document.getElementById('prev');
    const newer = document.getElementById('next');
    function show() {
      document.querySelectorAll('section.digest').forEach(function (section) {
        section.hidden = section.id !== weekEl.value;
      });
      newer.disabled = weekEl.selectedIndex === 0;
      older.disabled = weekEl.selectedIndex === weekEl.options.length - 1;
      window.scrollTo(0, 0);
    }
    function step(delta) {
      weekEl.selectedIndex = Math.max(0, Math.min(weekEl.options.length - 1, weekEl.selectedIndex + delta));
      show();
    }
    // Keep section links within the document, including in the Apps Script sandbox.
    document.addEventListener('click', function (event) {
      const anchor = event.target.closest('.jump a, .skip, .history-link');
      if (!anchor) return;
      const target = document.getElementById(anchor.getAttribute('href').slice(1));
      if (!target) return;
      event.preventDefault();
      target.setAttribute('tabindex', '-1');
      target.focus({ preventScroll: true });
      target.scrollIntoView({ behavior: 'instant', block: 'start' });
    });
    weekEl.addEventListener('change', show);
    older.addEventListener('click', function () { step(1); });
    newer.addEventListener('click', function () { step(-1); });
    show();
  </script>
</body>
</html>
"""


MAX_LIVE_EDITIONS = 12


def edition_day(file):
    return date.fromisoformat(file.stem.removeprefix('digest-')).isoformat()


def archive_links(day, archive):
    file_id = archive.get('editions', {}).get(day)
    if not file_id:
        return ''
    if not isinstance(file_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', file_id):
        raise ValueError(f'Invalid Drive file ID for {day}')
    return (link(f'https://drive.google.com/file/d/{file_id}/view', 'View file on Drive')
            + ' &middot; ' + link(f'https://drive.google.com/uc?export=download&amp;id={file_id}', 'Download HTML'))


def history_html(files, archive):
    years = {}
    for index, file in enumerate(files):
        day = edition_day(file)
        links = archive_links(day, archive)
        if not links:
            continue
        label = date.fromisoformat(day).strftime('%d %b %Y')
        location = ' &middot; In week picker' if index < MAX_LIVE_EDITIONS else ''
        years.setdefault(day[:4], []).append(f'<li><strong>Week ending {label}</strong>{location}<br>{links}</li>')
    body = ''.join(f'<h4>{year}</h4><ul>' + ''.join(items) + '</ul>' for year, items in years.items())
    pending = [edition_day(file) for file in files if edition_day(file) in archive.get('pending', [])]
    if pending:
        body += '<p>Weekly archive pending completion: ' + ', '.join(pending) + '.</p>'
    superseded = [f'<li>Original issue {html.escape(day)}: {archive_links(day, archive)}</li>'
                  for day in archive.get('superseded', []) if archive_links(day, archive)]
    if superseded:
        body += ('<details><summary>Earlier versions (superseded coverage windows)</summary>'
                 '<p>Preserved originals, not additional weekly editions. Use the corrected weeks above.</p><ul>'
                 + ''.join(superseded) + '</ul></details>')
    if not body:
        body = '<p>No downloadable editions published yet.</p>'
    return ('<section class="about history" id="history" aria-labelledby="history-title">'
            '<h3 id="history-title">History &amp; downloads</h3>'
            '<p>The latest 12 editions stay in the week picker. Download any saved edition as a standalone HTML file '
            'and open it in your browser. Drive access is required; if a direct download is blocked, use the Drive file menu.</p>'
            + body + '</section>')


def build_page(files, cfg, partner, archive, standalone=False):
    visible = files[:1] if standalone else files[:MAX_LIVE_EDITIONS]
    options, sections = [], []
    for index, file in enumerate(visible):
        day = edition_day(file)
        sid = f'w{day}'
        selected = ' selected' if index == 0 else ''
        latest = ' (latest)' if index == 0 and not standalone else ''
        label = date.fromisoformat(day).strftime('%d %b %Y')
        label = 'W/e ' + label
        options.append(f'<option value="{sid}"{selected}>{label}{latest}</option>')
        hidden = '' if index == 0 else ' hidden'
        download = archive_links(day, archive) if not standalone else ''
        download_html = f'<p class="edition-download">{download}</p>' if download else ''
        sections.append(f'<section class="digest" id="{sid}"{hidden}>\n{render(file.read_text(), sid)}\n{download_html}</section>')
    title = f"{cfg['name']} news digest" + (f' - {edition_day(visible[0])}' if standalone else '')
    metadata = json.dumps({
        'generated': date.today().isoformat(),
        'intent': 'Weekly editorial brief with news, separate client stories, short updates and expandable provenance',
        'dataSources': [{'type': 'file', 'path': str(file.relative_to(ROOT)) if file.is_relative_to(ROOT) else file.name} for file in visible],
        'archiveManifest': None if standalone else f'digests/{partner}/archive.json',
        'standalone': standalone,
        'sections': [{'id': f'w{edition_day(file)}', 'title': file.name} for file in visible]
                    + ([{'id': 'history', 'title': 'History & downloads',
                         'dataSources': [{'type': 'file', 'path': f'digests/{partner}/archive.json'}],
                         'producerNotes': 'All saved editions, newest first by year. Drive IDs are registered after upload.'}] if not standalone else [])
                    + [{'id': 'monitored-sources', 'title': 'Sources we search',
                        'dataSources': [{'type': 'file', 'path': f'partners/{partner}.json'}],
                        'producerNotes': 'Current configured feeds, all query/locale combinations and separate manual checks; not historical execution evidence.'}],
        'producerNotes': f'Rebuild with: python3 build_site.py {partner}. Client story headings determine grouping. More news uses topic headings and dated, factual bullets, with the newest 12 visible and the rest in a native disclosure. Empty categories are summarized, with exact coverage notes in About. Suggestions are expandable and explicitly labelled.',
    }, indent=2).replace('<', '\\u003c')
    page = (PAGE.replace('__TITLE__', html.escape(title)).replace('__META__', metadata)
            .replace('__OPTIONS__', '\n'.join(options)).replace('__SECTIONS__', '\n'.join(sections))
            .replace('__SOURCE_DIRECTORY__', source_directory(cfg))
            .replace('__HISTORY__', '' if standalone else history_html(files, archive))
            .replace('__HISTORY_NAV__', '' if standalone else '<a class="history-link" href="#history">History &amp; downloads</a>')
            .replace('__COUNT__', 'Standalone edition' if standalone else f'{len(visible)} editions on this page')
            .replace('__BUILT__', date.today().isoformat()))
    return page


def main():
    partner = sys.argv[1] if len(sys.argv) > 1 else 'capgemini'
    cfg = json.loads((ROOT / 'partners' / f'{partner}.json').read_text())
    digest_dir = ROOT / 'digests' / partner
    files = sorted(digest_dir.glob('digest-*.md'), reverse=True)
    if not files:
        sys.exit(f'no digests in {digest_dir}/')
    manifest = digest_dir / 'archive.json'
    archive = json.loads(manifest.read_text()) if manifest.exists() else {'editions': {}}
    files = [file for file in files if edition_day(file) not in archive.get('superseded', [])]
    if not files:
        sys.exit('No active editions remain after excluding superseded issues')
    # Do not drop an old edition from the live page before its Drive archive exists.
    missing = [edition_day(file) for file in files[MAX_LIVE_EDITIONS:]
               if not archive_links(edition_day(file), archive)]
    output = ROOT / 'site' / f'{partner}-news.html'
    snapshot_dir = ROOT / 'site' / 'archive' / partner
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    for file in files:
        # An in-progress week must not become an immutable completed-week archive.
        if edition_day(file) in archive.get('pending', []) or date.fromisoformat(edition_day(file)) > date.today():
            continue
        snapshot = snapshot_dir / f'{partner}-news-{edition_day(file)}.html'
        # Exclusive creation preserves the edition as first published.
        if not snapshot.exists():
            with snapshot.open('x') as handle:
                handle.write(build_page([file], cfg, partner, {}, standalone=True))
    if missing:
        sys.exit('Publish missing snapshots to Drive and register their IDs in archive.json before rebuilding: '
                 + ', '.join(missing))
    page = build_page(files, cfg, partner, archive)
    output.write_text(page)
    print(output, len(page.encode('utf-8')), 'bytes,', min(len(files), MAX_LIVE_EDITIONS), 'live editions')


if __name__ == '__main__':
    main()
