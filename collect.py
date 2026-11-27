#!/usr/bin/env python3
"""LYTORA RSS collector. Collects public feed metadata; does not republish full articles."""
import json, re, hashlib, urllib.parse, urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parent
SOURCES = json.loads((BASE / "sources.json").read_text(encoding="utf-8"))
OUT = BASE / "data" / "articles.json"

def clean(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()

def get_text(node, names):
    for name in names:
        el = node.find(name)
        if el is not None and el.text:
            return clean(el.text)
    return ""

def parse_feed(url, publisher, region, country=None):
    req = urllib.request.Request(url, headers={"User-Agent":"LYTORA-NewsCollector/0.1 (RSS reader)"})
    with urllib.request.urlopen(req, timeout=25) as response:
        raw = response.read()
    root = ET.fromstring(raw)
    items = root.findall(".//item")
    if not items:
        # Atom
        ns = {"a":"http://www.w3.org/2005/Atom"}
        items = root.findall(".//a:entry", ns)
    results = []
    for item in items:
        title = get_text(item, ["title", "{http://www.w3.org/2005/Atom}title"])
        link = get_text(item, ["link"])
        if not link:
            link_el = item.find("{http://www.w3.org/2005/Atom}link")
            if link_el is not None:
                link = link_el.attrib.get("href","")
        desc = get_text(item, ["description", "{http://www.w3.org/2005/Atom}summary", "{http://www.w3.org/2005/Atom}content"])
        pub = get_text(item, ["pubDate", "published", "{http://www.w3.org/2005/Atom}published", "{http://www.w3.org/2005/Atom}updated"])
        try:
            dt = parsedate_to_datetime(pub)
            if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
            published = dt.astimezone(timezone.utc).isoformat()
        except Exception:
            try:
                dt = datetime.fromisoformat(pub.replace("Z","+00:00"))
                published = dt.astimezone(timezone.utc).isoformat()
            except Exception:
                published = ""
        if not title or not link: continue
        uid = hashlib.sha256(link.encode("utf-8")).hexdigest()[:16]
        results.append({
            "id": uid, "title": title, "summary": desc[:500], "url": link,
            "publisher": publisher, "region": region, "country": country or "",
            "published_at": published, "collected_at": datetime.now(timezone.utc).isoformat()
        })
    return results

def google_news_url(country):
    q = urllib.parse.quote(f'"{country}" when:7d')
    return f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"

def main():
    all_items, errors = [], []
    for f in SOURCES["regional_feeds"]:
        try: all_items.extend(parse_feed(f["url"], f["name"], f["region"]))
        except Exception as e: errors.append({"source":f["name"],"error":str(e)[:180]})
    for country in SOURCES["priority_countries"]:
        try: all_items.extend(parse_feed(google_news_url(country), "Google News search", "国別", country))
        except Exception as e: errors.append({"source":country,"error":str(e)[:180]})
    dedup = {}
    for item in all_items:
        key = item["url"].split("?")[0]
        if key not in dedup: dedup[key] = item
    articles = list(dedup.values())
    articles.sort(key=lambda x: x["published_at"] or "", reverse=True)
    payload = {
        "project":"LYTORA", "generated_at":datetime.now(timezone.utc).isoformat(),
        "count":len(articles), "articles":articles, "source_errors":errors,
        "notice":"RSSから取得した見出し・短い要約・リンクの一覧です。記事本文の転載ではありません。内容の正確性と日本との関連性は公開前に編集確認してください。"
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(articles)} articles; {len(errors)} source errors.")

if __name__ == "__main__": main()
