# news.py — reference

Direct RSS aggregation across major crypto-news outlets. Uses
`feedparser`. No aggregator API (CryptoPanic / Bitget / CMC News all
require keys or a sign-up).

## Feeds

| Name | URL | Cadence |
|---|---|---|
| coindesk        | https://www.coindesk.com/arc/outboundfeeds/rss | continuous |
| cointelegraph   | https://cointelegraph.com/rss                  | continuous |
| decrypt         | https://decrypt.co/feed                        | continuous |
| bitcoinmagazine | https://bitcoinmagazine.com/feed               | continuous |
| theblock        | https://www.theblock.co/rss.xml                | continuous |

RSS items are typically published within minutes of the article going live. Each feed exposes ~15-30 recent items.

## Item fields

Per item:
- `title`, `url`, `published` (RFC822 string), `author`, `source` (feed name)
- `summary` is the RSS `<description>` (truncated to 400 chars; some feeds return HTML — agent should strip if needed)

`latest` sorts merged items by parsed `published` timestamp (descending) using `email.utils.parsedate_to_datetime`. Items without a parseable date sink to the bottom.

## Adding a feed

Append to the `FEEDS` dict in `scripts/news.py`. Any RSS 2.0 / Atom feed `feedparser` understands works.

Notable feeds **not** included by default:
- **CoinGecko News** — needs PRO API key.
- **CryptoPanic** — `/free/v1/` endpoints currently 404 without auth on the free tier; sign-up needed.
- **Reddit /r/cryptocurrency** — `.rss` works but item quality is low.
- **The Defiant**, **Blockworks**, **Messari** — RSS exists; add if needed.

## Search

`search QUERY` is naive substring match (case-insensitive) over title + summary + author of recently-pulled items. Not full-text search — for deeper queries use `multi-search` (Firecrawl / Serper) against the article URLs.
