
#!/usr/bin/env python3
"""LYTORA RSS collector."""
import json
import re
import html
import hashlib
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parent
SOURCES = json.loads(
    (BASE / "sources.json").read_text(encoding="utf-8")
)
OUT = BASE / "data" / "articles.json"

REGIONS = {
    "Namibia": "Africa",
    "Rwanda": "Africa",
    "Senegal": "Africa",
    "Botswana": "Africa",
    "Mauritania": "Africa",
    "Mongolia": "Asia",
    "Bhutan": "Asia",
    "Laos": "Asia",
    "Kyrgyzstan": "Asia",
    "Tajikistan": "Asia",
    "Papua New Guinea": "Oceania",
    "Fiji": "Oceania",
    "Moldova": "Europe",
    "Georgia": "Europe",
    "Armenia": "Europe",
    "Oman": "Middle East",
    "Uruguay": "Americas",
    "Paraguay": "Americas",
    "Suriname": "Americas",
    "Timor-Leste": "Asia",
}

def clean(value):
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]*>", " ", value)
    return re.sub(r"\s+", " ", value).strip()

def get_text(node, names):
    for name in names:
        element = node.find(name)
        if element is not None and element.text:
            return clean(element.text)
    return ""

def safe_url(url):
    try:
        parsed = urllib.parse.urlsplit(url.strip())
        return (
            parsed.scheme in ("https", "http")
            and bool(parsed.netloc)
            and not parsed.username
            and not parsed.password
        )
    except Exception:
        return False

def parse_date(value):
    if not value:
        return ""
    try:
        dt = parsedate_to_datetime(value)
    except Exception:
        try:
            dt = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )
        except Exception:
            return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()

def parse_feed(url, publisher, region, country=""):
    if not safe_url(url):
        raise ValueError("Invalid feed URL")

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "LYTORA-NewsCollector/1.0"
        }
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        raw = response.read(5_000_000)

    root = ET.fromstring(raw)
    items = root.findall(".//item")
    atom = False

    if not items:
        ns = {"a": "http://www.w3.org/2005/Atom"}
        items = root.findall(".//a:entry", ns)
        atom = True

    results = []

    for item in items:
        title = get_text(
            item,
            ["title", "{http://www.w3.org/2005/Atom}title"]
        )

        link = get_text(item, ["link"])

        if atom:
            link_element = item.find(
                "{http://www.w3.org/2005/Atom}link"
            )
            if link_element is not None:
                link = link_element.attrib.get("href", link)

        if not safe_url(link) or not title:
            continue

        summary = get_text(
            item,
            [
                "description",
                "{http://www.w3.org/2005/Atom}summary",
                "{http://www.w3.org/2005/Atom}content"
            ]
        )

        published = get_text(
            item,
            [
                "pubDate",
                "published",
                "{http://www.w3.org/2005/Atom}published",
                "{http://www.w3.org/2005/Atom}updated"
            ]
        )

        published_at = parse_date(published)

        uid = hashlib.sha256(
            link.encode("utf-8")
        ).hexdigest()[:16]

        results.append({
            "id": uid,
            "title": title[:300],
            "summary": summary[:500],
            "url": link,
            "publisher": publisher,
            "region": region,
            "country": country,
            "published_at": published_at,
            "collected_at": datetime.now(
                timezone.utc
            ).isoformat()
        })

    return results

def google_news_url(country):
    query = urllib.parse.quote(
        f'"{country}" when:7d'
    )
    return (
        "https://news.google.com/rss/search?q="
        + query
        + "&hl=en-US&gl=US&ceid=US:en"
    )

def main():
    all_items = []
    errors = []

    for country in SOURCES.get("priority_countries", []):
        try:
            region = REGIONS.get(country, "World")
            all_items.extend(
                parse_feed(
                    google_news_url(country),
                    "Google News",
                    region,
                    country
                )
            )
        except Exception as error:
            errors.append({
                "source": country,
                "error": str(error)[:180]
            })

    for feed in SOURCES.get("regional_feeds", []):
        try:
            all_items.extend(
                parse_feed(
                    feed["url"],
                    feed["name"],
                    feed["region"]
                )
            )
        except Exception as error:
            errors.append({
                "source": feed["name"],
                "error": str(error)[:180]
            })

    dedup = {}

    for item in all_items:
        key = item["url"].split("#")[0]
        if key not in dedup:
            dedup[key] = item

    articles = list(dedup.values())

    articles.sort(
        key=lambda item: item["published_at"] or "",
        reverse=True
    )

    payload = {
        "project": "LYTORA",
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "count": len(articles),
        "articles": articles,
        "source_errors": errors,
        "notice": (
            "RSSから取得した見出し・短い要約・リンクです。"
            "記事本文は転載していません。"
            "公開前に内容と日本との関連性を確認してください。"
        )
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(
        f"Saved {len(articles)} articles; "
        f"{len(errors)} source errors."
    )

if __name__ == "__main__":
    main()
