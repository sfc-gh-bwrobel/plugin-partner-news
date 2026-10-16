#!/usr/bin/env python3
"""Collect partner news from RSS / Google News into raw/<date>.json (stdlib only).

Usage: python3 collect.py partners/capgemini.json [--days 7]
"""
import argparse
import email.utils
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Section order for output; the first title regex that matches wins.
SECTION_PRIORITY = ["snowflake", "subsidiaries", "competitors", "leadership", "general"]
UA = {"User-Agent": "Mozilla/5.0 (partner-news collector)"}
CONTENT_NS = "{http://purl.org/rss/1.0/modules/content/}encoded"
MAX_PARA = 800  # longer "paragraphs" are usually link lists / sidebars


def http_get(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def fetch_items(url):
    root = ET.fromstring(http_get(url))
    for item in root.iter("item"):
        src = item.find("source")
        yield {
            "title": (item.findtext("title") or "").strip(),
            "link": (item.findtext("link") or "").strip(),
            "date": item.findtext("pubDate") or "",
            "publisher": src.text.strip() if src is not None and src.text else "",
            "body": item.findtext(CONTENT_NS) or "",  # full text on capgemini.com feeds
        }


def decode_google_news(link):
    """Resolve a news.google.com/rss/articles/... link to the publisher URL.

    Undocumented Google endpoint (same call the web UI makes); may break without notice.
    """
    if "news.google.com/rss/articles/" not in link:
        return link
    aid = link.split("/articles/")[1].split("?")[0]
    page = http_get(f"https://news.google.com/rss/articles/{aid}").decode("utf8", "ignore")
    sg = re.search(r'data-n-a-sg="([^"]+)"', page).group(1)
    ts = re.search(r'data-n-a-ts="([^"]+)"', page).group(1)
    inner = ('["garturlreq",[["X","X",["X","X"],null,null,1,1,"US:en",null,1,null,null,null,null,null,0,1],'
             f'"X","X",1,[1,1,1],1,1,null,0,0,null,0],"{aid}",{ts},"{sg}"]')
    body = "f.req=" + urllib.parse.quote(json.dumps([[["Fbv4je", inner]]]))
    resp = http_get("https://news.google.com/_/DotsSplashUi/data/batchexecute", body.encode(),
                    {"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"}).decode("utf8")
    return json.loads(json.loads(resp.split("\n\n")[1])[:-2][0][2])[1]


def paragraphs(page):
    page = re.sub(r"(?is)<(script|style|nav|header|footer|aside)[^>]*>.*?</\1>", " ", page)
    for p in re.findall(r"(?is)<p[^>]*>(.*?)</p>", page):
        text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", p))).strip()
        if text and len(text) <= MAX_PARA:
            yield text


def co_mention(page, a_rx, b_rx):
    """First paragraph mentioning both terms, else None."""
    return next((p for p in paragraphs(page) if a_rx.search(p) and b_rx.search(p)), None)


def google_news_url(q, days, loc):
    params = {"q": f"{q} when:{days}d", **loc}
    return "https://news.google.com/rss/search?" + urllib.parse.urlencode(params)


def dedupe_key(title):
    title = re.sub(r" - [^-]+$", "", title)  # strip " - Publisher" suffix
    return re.sub(r"\W+", " ", title.lower()).strip()


def parse_date(s):
    try:
        return email.utils.parsedate_to_datetime(s).astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("--days", type=int, default=7)
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text())
    noise = re.compile(cfg["noise_regex"], re.I)
    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)

    sources = [(f["id"], f["section"], f["url"]) for f in cfg["feeds"]]
    gn = cfg.get("google_news", {})
    for query in gn.get("queries", []):
        for loc in gn.get("locales", []):
            sources.append((f"gnews-{query['section']}-{loc['gl']}", query["section"],
                            google_news_url(query["q"], args.days, loc)))

    title_rx = {s: re.compile(cfg.get("section_title_regex", {})[s], re.I)
                for s in SECTION_PRIORITY if s in cfg.get("section_title_regex", {})}
    # Partner name plus subsidiaries (e.g. WNS, Kipi) count as "about the partner".
    partner_rx = re.compile(cfg.get("aliases_regex", re.escape(cfg["name"])), re.I)
    sub_rx = title_rx.get("subsidiaries")
    snow_rx = re.compile(r"\bSnowflake\b")  # case-sensitive: skips "snowflake" as a word
    items, stats = {}, {"raw": 0, "noise": 0, "old": 0, "off_topic": 0, "body_checked": 0, "errors": []}
    for feed_id, section, url in sources:
        try:
            fetched = list(fetch_items(url))
        except Exception as e:  # keep going if one feed fails
            stats["errors"].append(f"{feed_id}: {e}")
            continue
        for it in fetched:
            stats["raw"] += 1
            if noise.search(it["title"]):
                stats["noise"] += 1
                continue
            dt = parse_date(it["date"])
            if dt and dt < cutoff:
                stats["old"] += 1
                continue
            # Google News matches queries loosely, so the section comes from the title.
            assigned = next((s for s, rx in title_rx.items() if rx.search(it["title"])), "general")
            # Targeted sections must be about the partner itself, not an ex-employee elsewhere.
            if assigned != "general" and not partner_rx.search(it["title"]):
                assigned = "general"
            # Snowflake mentions: check the article body, not just the title.
            evidence = None
            if assigned != "snowflake" and (section == "snowflake" or it["body"]):
                page = it["body"]
                if not page:
                    stats["body_checked"] += 1
                    time.sleep(1)  # Google returns 429 on rapid decode calls
                    try:
                        it["link"] = decode_google_news(it["link"])
                        page = http_get(it["link"]).decode("utf8", "ignore")
                    except Exception as e:
                        stats["errors"].append(f"body {it['title'][:50]}: {e}")
                evidence = co_mention(page, partner_rx, snow_rx)
                if evidence:
                    assigned = "snowflake"
            # Subsidiary mentions inside partner articles (full text from partner feeds).
            if assigned == "general" and sub_rx and it["body"]:
                evidence = next((p for p in paragraphs(it["body"]) if sub_rx.search(p)), None)
                if evidence:
                    assigned = "subsidiaries"
            if section != "general" and assigned == "general":
                stats["off_topic"] += 1  # extra query returned an unrelated article
                continue
            key = dedupe_key(it["title"])
            prev = items.get(key)
            if prev and not (assigned == "snowflake" and prev["section"] != "snowflake"):
                continue
            it.pop("body")
            items[key] = {**it, "feed": feed_id, "section": assigned, "evidence": evidence,
                          "date": dt.isoformat() if dt else it["date"]}

    out = sorted(items.values(), key=lambda i: (SECTION_PRIORITY.index(i["section"]), i["date"]), reverse=False)
    out_dir = Path(args.config).resolve().parent.parent / "raw" / Path(args.config).stem
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{datetime.now():%Y-%m-%d}.json"
    path.write_text(json.dumps({"partner": cfg["name"], "stats": stats,
                                "manual_checks": cfg.get("manual_checks", []),
                                "items": out}, ensure_ascii=False, indent=1))

    by_section = {s: sum(1 for i in out if i["section"] == s) for s in SECTION_PRIORITY}
    print(f"{path}\nraw={stats['raw']} noise={stats['noise']} old={stats['old']} off_topic={stats['off_topic']} body_checked={stats['body_checked']} kept={len(out)} {by_section}")
    for err in stats["errors"]:
        print("ERROR", err, file=sys.stderr)


if __name__ == "__main__":
    main()
