"""news_fetcher: use RSS/feeds to reliably collect China-related news from mainstream sources.

This replaces brittle HTML scraping with feedparser-based RSS parsing and simple keyword
filtering for "china". Feeds are checked in order and duplicates are removed.
"""
import feedparser
import requests

FEEDS = [
    ("CNN", "https://rss.cnn.com/rss/edition_world.rss"),
    ("BBC", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("Google News", "https://news.google.com/rss/search?q=China&hl=en-US&gl=US&ceid=US:en"),
]

# simple in-memory resolution cache for redirect unwrapping during a run
_RESOLVE_CACHE = {}


def parse_feed(source_name, feed_url):
    parsed = feedparser.parse(feed_url)
    articles = []
    for entry in parsed.entries:
        title = entry.get('title', '').strip()
        link = entry.get('link', '').strip()
        summary = entry.get('summary', '') or entry.get('description', '') or ''
        published = entry.get('published', '') or entry.get('pubDate', '')
        text = (title + ' ' + summary).lower()
        # simple keyword filter for China-related content
        if 'china' in text or 'chinese' in text:
            # classify by URL domain where possible
            try:
                from urllib.parse import urlparse, parse_qs, unquote
                import re
                # Prefer the entry's source.href when Google News wraps links
                candidate = ''
                source_field = entry.get('source')
                if isinstance(source_field, dict) and source_field.get('href'):
                    candidate = source_field.get('href')

                # If not available, try to extract an external URL from the summary HTML
                if not candidate:
                    summary_html = entry.get('summary', '') or ''
                    urls = re.findall(r'https?://[^\s"<>]+', summary_html)
                    # prefer the first url that is NOT news.google.com
                    for u in urls:
                        if 'news.google.com' not in u:
                            candidate = u
                            break
                    if not candidate and urls:
                        candidate = urls[0]

                # still not found: fallback to query params (some redirects use ?url=...)
                if not candidate:
                    parsed_link = urlparse(link)
                    qs = parse_qs(parsed_link.query)
                    for key in ('url', 'u', 'q'):
                        if key in qs and qs[key]:
                            candidate = qs[key][0]
                            break

                # final fallback: unquote the link or use its netloc
                if not candidate:
                    candidate = unquote(link)

                netloc = urlparse(candidate).netloc.lower() if candidate else ''
                # if candidate is a Google News wrapper, try to resolve the real target URL (cached)
                canonical = candidate or link
                try:
                    if 'news.google.com' in netloc or 'news.google' in canonical:
                        if canonical in _RESOLVE_CACHE:
                            final = _RESOLVE_CACHE[canonical]
                        else:
                            # perform a GET to follow redirects and discover the publisher URL
                            resp = requests.get(canonical, timeout=6, headers={"User-Agent": "newsbridge/1.0"}, allow_redirects=True)
                            final = resp.url or canonical
                            _RESOLVE_CACHE[canonical] = final
                        netloc = urlparse(final).netloc.lower() if final else netloc
                except Exception:
                    # ignore resolution failures and keep original netloc
                    pass
                # remove common www
                if netloc.startswith('www.'):
                    netloc = netloc[4:]
            except Exception:
                netloc = ''

            def map_domain_to_source(domain: str):
                if not domain:
                    return source_name
                # common mappings
                if domain.endswith('cnn.com'):
                    return 'CNN'
                if domain.endswith('bbc.co.uk') or domain.endswith('bbc.com'):
                    return 'BBC'
                if domain.endswith('reuters.com'):
                    return 'Reuters'
                if domain.endswith('nytimes.com'):
                    return 'The New York Times'
                if domain.endswith('bloomberg.com'):
                    return 'Bloomberg'
                if domain.endswith('nbcnews.com') or domain.endswith('nbc.com'):
                    return 'NBC News'
                if domain.endswith('politico.com'):
                    return 'Politico'
                if domain.endswith('wsj.com') or domain.endswith('thewallstreetjournal.com'):
                    return 'Wall Street Journal'
                if domain.endswith('scmp.com'):
                    return 'South China Morning Post'
                if domain.endswith('apnews.com'):
                    return 'AP News'
                if domain.endswith('foxnews.com'):
                    return 'Fox News'
                if domain.endswith('newsweek.com'):
                    return 'Newsweek'
                # fallback: use domain as source if short
                return domain

            detected_source = map_domain_to_source(netloc)
            articles.append({
                'title': title,
                'url': link,
                'summary': summary,
                'published': published,
                'source': detected_source,
                'feed_source': source_name,
            })
    return articles


def get_all_china_news():
    seen = set()
    results = []
    for name, url in FEEDS:
        try:
            for a in parse_feed(name, url):
                if a['url'] and a['url'] not in seen:
                    seen.add(a['url'])
                    results.append(a)
        except Exception:
            # keep going if one feed fails
            continue
    return results
