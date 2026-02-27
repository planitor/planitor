"""Scrape deiliskipulag plan metadata and PDF URLs from Skipulagsstofnun.

For each skipnr in the shapefile, fetches the display.aspx page and extracts:
- Plan metadata (heiti, sveitarfélag, approval date, málsmeðferð, case number)
- PDF document URLs with labels and file sizes

Usage:
    docker compose exec -T planitor python scripts/scrape_deiliskipulag.py
    docker compose exec -T planitor python scripts/scrape_deiliskipulag.py --limit 10
    docker compose exec -T planitor python scripts/scrape_deiliskipulag.py --dry-run
"""

import argparse
import datetime as dt
import logging
import re
import sys
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://skipulagsaaetlanir.skipulagsstofnun.is/skipulagvefur"
DISPLAY_URL = f"{BASE_URL}/display.aspx?numer={{}}"
DOC_URL = f"{BASE_URL}/DisplayDoc.aspx?itemid={{}}"

# Map document labels to our doc_type values
DOC_TYPE_MAP = {
    "skipulagsgreinargerð": "greinargerð",
    "skipulagsgreinarger": "greinargerð",
    "greinargerð": "greinargerð",
    "skýrsla/greinargerð": "greinargerð",
    "skýrsla": "greinargerð",
    "skipulagsuppdráttur": "uppdráttur",
    "uppdráttur": "uppdráttur",
    "skýringaruppdráttur": "skýringaruppdráttur",
}


class SkipulagPageParser(HTMLParser):
    """Parse the display.aspx page for metadata and document links."""

    def __init__(self):
        super().__init__()
        self.metadata = {}
        self.documents = []
        self._in_td1 = False
        self._in_td2 = False
        self._in_thumb_title = False
        self._current_label = None
        self._current_td_text = ""
        self._thumb_text = ""
        self._thumb_href = None

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        css_class = attrs_dict.get("class", "")

        if tag == "td" and css_class == "ss_infoTD1":
            self._in_td1 = True
            self._current_td_text = ""
        elif tag == "td" and css_class == "ss_infoTD2" and self._current_label:
            self._in_td2 = True
            self._current_td_text = ""
        elif tag == "td" and css_class == "ss_thumbTitle":
            self._in_thumb_title = True
            self._thumb_text = ""
            self._thumb_href = None
        elif tag == "a" and self._in_thumb_title:
            href = attrs_dict.get("href", "")
            if "DisplayDoc.aspx" in href:
                self._thumb_href = href

    def handle_data(self, data):
        if self._in_td1:
            self._current_td_text += data
        elif self._in_td2:
            self._current_td_text += data
        elif self._in_thumb_title:
            self._thumb_text += data

    def handle_endtag(self, tag):
        if tag == "td" and self._in_td1:
            self._in_td1 = False
            self._current_label = self._current_td_text.strip()
        elif tag == "td" and self._in_td2:
            self._in_td2 = False
            value = self._current_td_text.strip()
            if self._current_label and value:
                self.metadata[self._current_label] = value
            self._current_label = None
        elif tag == "td" and self._in_thumb_title:
            self._in_thumb_title = False
            self._finalize_document()

    def _finalize_document(self):
        if not self._thumb_href:
            return
        text = self._thumb_text.strip()
        # Extract label (first line before "Sækja")
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        label = lines[0] if lines else ""
        # Extract file size from pattern like "(11,24 MB)"
        size_match = re.search(r"\((\d+[,\.]\d+)\s*MB\)", text)
        file_size_mb = None
        if size_match:
            file_size_mb = float(size_match.group(1).replace(",", "."))

        # Extract itemid from href
        itemid_match = re.search(r"itemid=(\w+)", self._thumb_href)
        if itemid_match:
            source_url = DOC_URL.format(itemid_match.group(1))
        else:
            source_url = self._thumb_href

        # Normalize label to doc_type
        label_lower = label.lower().strip()
        doc_type = None
        for key, value in DOC_TYPE_MAP.items():
            if label_lower.startswith(key):
                doc_type = value
                break
        if doc_type is None:
            doc_type = label_lower or "unknown"

        self.documents.append(
            {
                "label": label,
                "doc_type": doc_type,
                "source_url": source_url,
                "file_size_mb": file_size_mb,
            }
        )


def parse_date(s):
    """Parse date string like '19.03.2020'."""
    if not s:
        return None
    match = re.match(r"(\d{2})\.(\d{2})\.(\d{4})", s.strip())
    if match:
        day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
        try:
            return dt.date(year, month, day)
        except ValueError:
            return None
    return None


def fetch_plan_page(skipnr):
    """Fetch and parse a display.aspx page for a given skipnr."""
    url = DISPLAY_URL.format(skipnr)
    req = Request(url, headers={"User-Agent": "planitor/1.0 (deiliskipulag scraper)"})
    try:
        with urlopen(req, timeout=30) as response:
            html = response.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError, TimeoutError) as e:
        logger.warning("Failed to fetch skipnr=%d: %s", skipnr, e)
        return None, None

    parser = SkipulagPageParser()
    parser.feed(html)
    return parser.metadata, parser.documents


def get_all_skipnr():
    """Get all skipnr values from file or shapefile.

    Prefers scripts/skipnr_list.txt (pre-extracted) to avoid loading
    the full shapefile + GDAL into the scraper process.
    Generate the file with:
        python -c "import skipulagsstofnun; ..."
    """
    list_file = Path(__file__).resolve().parent / "skipnr_list.txt"
    if list_file.exists():
        skipnrs = [int(line.strip()) for line in list_file.read_text().splitlines() if line.strip()]
        logger.info("Loaded %d skipnr values from %s", len(skipnrs), list_file.name)
        return sorted(skipnrs)

    import skipulagsstofnun
    db = skipulagsstofnun.plans
    if db._plans is None:
        db._load()
    return sorted(db._plans.keys())


def main():
    parser = argparse.ArgumentParser(description="Scrape deiliskipulag plan metadata")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of plans to scrape")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be scraped")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between requests (seconds)")
    parser.add_argument(
        "--skip-existing", action="store_true", default=True,
        help="Skip plans already in the database (default: true)",
    )
    args = parser.parse_args()

    from planitor.database import db_context
    from planitor.models import DeiliskipulagPlan, DeiliskipulagDocument

    all_skipnr = get_all_skipnr()
    logger.info("Found %d skipnr values in shapefile", len(all_skipnr))

    if args.dry_run:
        for skipnr in all_skipnr[:20]:
            logger.info("  [dry-run] skipnr=%d", skipnr)
        if len(all_skipnr) > 20:
            logger.info("  ... and %d more", len(all_skipnr) - 20)
        return

    processed = 0
    created = 0
    skipped = 0
    failed = 0

    with db_context() as db:
        existing_skipnrs = set()
        if args.skip_existing:
            existing_skipnrs = set(
                r[0] for r in db.query(DeiliskipulagPlan.skipnr).all()
            )
            logger.info("Found %d existing plans in DB", len(existing_skipnrs))

    for skipnr in all_skipnr:
        if args.limit and processed >= args.limit:
            break

        if skipnr in existing_skipnrs:
            skipped += 1
            continue

        processed += 1
        metadata, documents = fetch_plan_page(skipnr)

        if metadata is None:
            failed += 1
            continue

        heiti = metadata.get("Heiti", "")
        sveitarfelag = metadata.get("Sveitarfélag", "")
        # Strip municipality code prefix (e.g. "0000 Reykjavík" → "Reykjavík")
        if sveitarfelag and " " in sveitarfelag:
            sveitarfelag = sveitarfelag.split(" ", 1)[1]
        dagsleidrett = parse_date(metadata.get("Samþykkt/Staðfest", ""))
        malsmed = metadata.get("Málsmeðferð", "")
        numer_mals = metadata.get("Númer máls", "")

        with db_context() as db:
            plan = DeiliskipulagPlan(
                skipnr=skipnr,
                heiti=heiti,
                sveitarfelag=sveitarfelag,
                dagsleidrett=dagsleidrett,
                malsmed=malsmed,
                numer_mals=numer_mals or None,
            )
            db.merge(plan)
            db.flush()

            for doc in documents:
                existing_doc = (
                    db.query(DeiliskipulagDocument)
                    .filter(
                        DeiliskipulagDocument.skipnr == skipnr,
                        DeiliskipulagDocument.source_url == doc["source_url"],
                    )
                    .first()
                )
                if not existing_doc:
                    db.add(
                        DeiliskipulagDocument(
                            skipnr=skipnr,
                            doc_type=doc["doc_type"],
                            source_url=doc["source_url"],
                            file_size_mb=doc["file_size_mb"],
                        )
                    )
            db.commit()
            created += 1

        if processed % 50 == 0:
            logger.info(
                "[%d/%d] processed=%d created=%d skipped=%d failed=%d",
                processed,
                len(all_skipnr),
                processed,
                created,
                skipped,
                failed,
            )

        time.sleep(args.delay)

    logger.info(
        "Done. processed=%d created=%d skipped=%d failed=%d",
        processed,
        created,
        skipped,
        failed,
    )


if __name__ == "__main__":
    main()
