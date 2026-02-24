# CLAUDE.md - Planitor Development Guide

Planitor is a business intelligence service for Icelandic planning, property, transport, and construction data. It aggregates meeting minutes from municipal councils into a searchable database.

## Tech Stack

- **Backend**: FastAPI + SQLAlchemy 1.3 + PostgreSQL
- **Scraping**: Scrapy with custom pipelines
- **Search**: PostgreSQL full-text search with tsvector
- **Lemmatization**: lemma.solberg.is API (Icelandic text processing)
- **Image proxy**: imgproxy (via `planitor/imgproxy.py`)
- **Background jobs**: Dramatiq with Redis
- **Deployment**: Docker container in `~/mediaserver/docker-compose.yml`

## Project Structure

```
planitor/
├── scrape/
│   ├── spiders/           # Scrapy spiders for each data source
│   │   ├── reykjavik_skipulagsfulltrui.py
│   │   ├── reykjavik_byggingarfulltrui.py
│   │   ├── reykjavik_byggingarfulltrui_pdf.py  # PDF-based (2021+)
│   │   ├── reykjavik_skipulagsrad.py
│   │   ├── arborg.py
│   │   └── hafnarfjordur.py
│   ├── pipelines.py       # DatabasePipeline - saves scraped data
│   └── settings.py
├── planitor/
│   ├── postprocess.py     # process_minutes() - creates Cases, Minutes
│   ├── crud/city.py       # create_minute(), get_or_create_case()
│   ├── language/
│   │   ├── lemma_api.py   # HTTP client for lemma.solberg.is
│   │   └── search.py      # lemmatize_and_index() for tsvector
│   ├── imgproxy.py        # Image URL signing
│   └── models/            # SQLAlchemy models
└── tests/
```

## Running Spiders

Spiders run on the **host machine** (not inside Docker) because they need network access and the database runs on localhost.

### Execute a spider

```bash
cd ~/mediaserver/planitor

# Run specific spider
docker compose exec -T planitor scrapy crawl reykjavik_byggingarfulltrui_pdf

# Run with year filter (if spider supports it)
docker compose exec -T planitor scrapy crawl reykjavik_byggingarfulltrui_pdf -a year=2024

# Run with limit
docker compose exec -T planitor scrapy crawl reykjavik_byggingarfulltrui_pdf -a limit=5

# List all spiders
docker compose exec -T planitor scrapy list
```

### Spider output flow

1. Spider yields item dict with `name`, `start`, `url`, `description`, `minutes[]`
2. `DatabasePipeline.process_item()` in `scrape/pipelines.py`:
   - Gets/creates Municipality and Council
   - Gets/creates Meeting
   - Calls `process_minutes()` to create Cases and Minutes
3. `postprocess.py` `process_minutes()`:
   - For each minute, calls `create_minute()`
   - Geocodes addresses via iceaddr
   - Indexes text with lemmatization for search
4. `crud/city.py` `create_minute()`:
   - Links minute to case (by serial number)
   - Updates case status from remarks text

## Spider Development Workflow

### 1. Identify the data source

- Reykjavík HTML: `gamli.rvk.is` (old format)
- Reykjavík PDFs: `reykjavik.is/byggingarmal/fundargerdir-*` (2021+)
- Other municipalities: OneSystem API or custom

### 2. Create/modify spider

Each spider must define:
```python
class MySpider(scrapy.Spider):
    name = "my_spider"
    municipality_slug = "reykjavik"  # matches Municipality table
    council_type_slug = "skipulagsfulltrui"  # matches Council table
```

And yield items matching this structure:
```python
{
    "name": "1234",  # Meeting number
    "start": datetime,
    "url": "https://...",
    "description": "Attendees: ...",
    "minutes": [
        {
            "serial": "1",  # Item number on agenda
            "case_serial": "USK24010123",  # Unique case ID
            "case_address": "Laugavegur 1",
            "headline": "Permit for...",
            "inquiry": "Application text...",
            "remarks": "Samþykkt.",  # Decision
            "entities": [],  # Kennitalas found
        }
    ]
}
```

### 3. Test with limit

```bash
docker compose exec -T planitor scrapy crawl my_spider -a limit=1
```

### 4. Check database

```bash
psql postgresql://planitor:password@localhost:5432/planitor -c \
  "SELECT id, name, start FROM meetings ORDER BY id DESC LIMIT 5"
```

### 5. Debug parsing issues

```python
# In spider, add logging:
self.logger.info(f"Parsed {len(minutes)} items from {url}")

# Check scrapy output for errors
docker compose exec -T planitor scrapy crawl my_spider 2>&1 | grep -i error
```

## Common Issues & Fixes

### "DropItem: Meeting X already has minutes"
The meeting was already scraped. This is normal - prevents duplicate imports.

### "case.updated is None" comparison error
Fixed in commit `297c2c4`. Ensure null checks before datetime comparisons.

### Pipeline returns None
Must raise `DropItem` instead of returning `None`. Fixed in commit `92fa4f4`.

### PDF parsing issues
- Check pdfplumber extraction: `pdf.pages[0].extract_text()`
- PDF format may have changed - compare old vs new samples
- Regex patterns for item extraction may need updating

### Rate limiting on lemma API
Use `LEMMA_API_KEY` env var to bypass rate limits (set in `.env`).

## Redeploying

After code changes:

```bash
cd ~/mediaserver
docker compose up -d --build planitor
```

The container rebuilds and restarts automatically.

## Database

- Host: `localhost:5432`
- Database: `planitor`
- User: `planitor`
- Password: `password`

```bash
# Connect
psql postgresql://planitor:password@localhost:5432/planitor

# Useful queries
SELECT COUNT(*) FROM minutes;
SELECT COUNT(*) FROM cases;
SELECT m.name, m.start, COUNT(min.id) FROM meetings m 
  LEFT JOIN minutes min ON min.meeting_id = m.id 
  GROUP BY m.id ORDER BY m.start DESC LIMIT 10;
```

## Key Environment Variables

```
DATABASE_URL=postgresql://planitor:password@localhost:5432/planitor
LEMMA_API_KEY=...          # Bypass rate limits on lemma.solberg.is
IMGPROXY_KEY=...           # For image URL signing
IMGPROXY_SALT=...
```

## External Services

- **lemma.solberg.is**: Icelandic lemmatization API
  - `/api/text` - lemmatize full text
  - `/api/lemmatize` - single word
  - Rate limit: 100 req/min (bypassed with API key)

- **imgproxy.plex.uno**: Image resizing/optimization proxy

- **iceaddr**: Python library for Icelandic address geocoding
