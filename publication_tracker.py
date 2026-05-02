"""
Publication Impact Tracker
Finds and categorizes external references to a given article.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, quote_plus
import time
import csv

# Article we are tracking
SOURCE_URL = "https://www.nasa.gov/news-release/nasa-welcomes-record-setting-artemis-ii-moonfarers-back-to-earth/"
SEARCH_QUERY = "Artemis II NASA splashdown April 2026"

# URLs found manually
KNOWN_REFERENCES = [
    "https://www.space.com/news/live/artemis-2-nasa-moon-mission-updates-april-10-2026",
    "https://www.pbs.org/newshour/science/watch-live-artemis-ii-crew-splashes-down-on-earth-after-historic-trip-around-the-moon",
    "https://www.cnn.com/2026/04/10/science/live-news/artemis-2-splashdown-astronauts-return",
    "https://www.nbcnews.com/science/space/live-blog/nasa-artemis-ii-splashdown-time-astronauts-live-updates-rcna266591",
    "https://www.gov.ca.gov/2026/04/10/governor-newsom-welcomes-nasas-artemis-ii-crew-back-to-earth-touching-down-in-the-golden-state/",
    "https://en.wikipedia.org/wiki/Artemis_II",
    "https://en.wikipedia.org/wiki/Artemis_program",
]


def get_platform(url):
    domain = urlparse(url).netloc.lower()

    if "reddit.com" in domain:
        return "Reddit"
    elif "wikipedia.org" in domain:
        return "Wikipedia"
    elif "youtube.com" in domain:
        return "YouTube"
    elif "twitter.com" in domain or "x.com" in domain:
        return "Twitter/X"
    elif "linkedin.com" in domain:
        return "LinkedIn"
    elif any(x in domain for x in ["bbc.", "cnn.", "nbc.", "pbs.", "reuters.", "apnews."]):
        return "Major News"
    elif any(x in domain for x in ["space.com", "nasaspaceflight.", "arstechnica."]):
        return "Science Media"
    elif ".gov" in domain:
        return "Government"
    else:
        return "Other"


def get_usage_type(text, url):
    text = text.lower()
    domain = urlparse(url).netloc.lower()

    if "wikipedia.org" in domain:
        return "Encyclopedia reference"
    elif ".gov" in domain:
        return "Official response"
    elif any(x in text for x in ["live", "update", "breaking"]):
        return "Live coverage"
    elif any(x in text for x in ["according to nasa", "nasa said", "nasa reports"]):
        return "Direct citation"
    elif any(x in text for x in ["analysis", "what it means", "explains"]):
        return "Analysis"
    elif any(x in text for x in ["summary", "recap", "overview"]):
        return "Summary"
    else:
        return "Mention / reference"


def fetch_page_title(url):
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        soup = BeautifulSoup(resp.text, "html.parser")
        return soup.title.get_text().strip() if soup.title else urlparse(url).netloc
    except Exception:
        return urlparse(url).netloc


def search_reddit(query, limit=8):
    """Search Reddit using public JSON API."""
    results = []
    url = f"https://www.reddit.com/search.json?q={quote_plus(query)}&sort=relevance&limit={limit}"
    try:
        resp = requests.get(url, headers={"User-Agent": "PublicationTracker/1.0"}, timeout=10)
        data = resp.json()
        for post in data["data"]["children"]:
            p = post["data"]
            results.append({
                "url": "https://reddit.com" + p["permalink"],
                "title": p["title"],
                "snippet": f"r/{p['subreddit']} | {p['score']} upvotes | {p['num_comments']} comments"
            })
    except Exception as e:
        print(f"Reddit search failed: {e}")
    return results


def main():
    print("=== Publication Impact Tracker ===")
    print(f"Tracking: {SOURCE_URL}\n")

    all_results = []
    seen_urls = set()

    # Step 1: Process manually collected URLs
    print("Step 1: Analyzing manually collected references...")
    for url in KNOWN_REFERENCES:
        if url in seen_urls:
            continue
        seen_urls.add(url)

        title = fetch_page_title(url)
        platform = get_platform(url)
        usage = get_usage_type(title, url)

        all_results.append({
            "url": url,
            "title": title,
            "platform": platform,
            "usage_type": usage,
            "found_by": "manual"
        })
        print(f"  OK  {platform} | {usage} | {urlparse(url).netloc}")
        time.sleep(0.5)

    # Step 2: Search Reddit automatically
    print(f"\nStep 2: Searching Reddit for '{SEARCH_QUERY}'...")
    reddit_posts = search_reddit(SEARCH_QUERY)

    for post in reddit_posts:
        if post["url"] in seen_urls:
            continue
        seen_urls.add(post["url"])

        platform = get_platform(post["url"])
        usage = get_usage_type(post["title"], post["url"])

        all_results.append({
            "url": post["url"],
            "title": post["title"],
            "platform": platform,
            "usage_type": usage,
            "found_by": "reddit_api"
        })
        print(f"  OK  Reddit | {usage} | {post['title'][:50]}")

    # Step 3: Print summary
    print(f"\n=== Results: {len(all_results)} references found ===\n")

    platforms = {}
    usage_types = {}
    for r in all_results:
        platforms[r["platform"]] = platforms.get(r["platform"], 0) + 1
        usage_types[r["usage_type"]] = usage_types.get(r["usage_type"], 0) + 1

    print("By platform:")
    for p, count in sorted(platforms.items(), key=lambda x: -x[1]):
        print(f"  {p}: {count}")

    print("\nBy usage type:")
    for u, count in sorted(usage_types.items(), key=lambda x: -x[1]):
        print(f"  {u}: {count}")

    # Step 4: Save to CSV
    with open("references.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["url", "title", "platform", "usage_type", "found_by"])
        writer.writeheader()
        writer.writerows(all_results)
    print("\nSaved to references.csv")


if __name__ == "__main__":
    main()
