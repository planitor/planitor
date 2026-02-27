"""Load HMS kaupskrá (property transaction data) into the property_transactions table.

Downloads CSV from HMS public URL, parses addresses via iceaddr geocoding,
multiplies kaupverd × 1000 for full ISK, and bulk inserts.

CSV columns: FAERSLUNUMER;EMNR;SKJALANUMER;FASTNUM;HEIMILISFANG;POSTNR;HEINUM;
SVFN;SVEITARFELAG;UTGDAG;THINGLYSTDAGS;KAUPVERD;FASTEIGNAMAT;...;BYGGAR;...;
EINFLM;...;FJHERB;TEGUND;FULLBUID;ONOTHAEFUR_SAMNINGUR

Usage:
    python scripts/load_kaupskra.py --csv ~/Downloads/kaupskra.csv
    python scripts/load_kaupskra.py --csv ~/Downloads/kaupskra.csv --no-geocode
"""

import argparse
import csv
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://planitor:password@localhost:5432/planitor"
)


def parse_date(s):
    """Parse HMS date string like '2006-05-08 00:00:00.0' to 'YYYY-MM-DD' or None."""
    if not s or not s.strip():
        return None
    s = s.strip()
    # Take just the date portion
    return s[:10] if len(s) >= 10 else None


def parse_rows(csv_path: str, geocode: bool = True):
    """Parse the HMS CSV and yield dicts ready for insertion."""
    from planitor.geo import get_address_lookup_params, lookup_address

    with open(csv_path, newline="", encoding="ISO-8859-1") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            faerslunumer = row.get("FAERSLUNUMER", "").strip()
            if not faerslunumer:
                continue

            heimilisfang = row.get("HEIMILISFANG", "").strip()
            kaupverd_raw = row.get("KAUPVERD", "").strip()
            kaupverd = int(float(kaupverd_raw) * 1000) if kaupverd_raw else None

            # Parse dates — UTGDAG and THINGLYSTDAGS are datetime strings
            utgefid = parse_date(row.get("UTGDAG", ""))
            thinglyst = parse_date(row.get("THINGLYSTDAGS", ""))

            flatarmal = row.get("EINFLM", "").strip()
            fjoldi = row.get("FJHERB", "").strip()
            byggar = row.get("BYGGAR", "").strip()
            sveitarfelag = row.get("SVEITARFELAG", "").strip()

            address_id = None
            if geocode and heimilisfang:
                try:
                    street, number, letter = get_address_lookup_params(heimilisfang)
                    match = lookup_address(street, number, letter, sveitarfelag)
                    if match:
                        address_id = match["hnitnum"]
                except Exception:
                    pass

            yield {
                "faerslunumer": int(faerslunumer),
                "heinum": row.get("HEINUM", "").strip() or None,
                "fastnum": row.get("FASTNUM", "").strip() or None,
                "heimilisfang": heimilisfang or None,
                "kaupverd": kaupverd,
                "tegund": row.get("TEGUND", "").strip() or None,
                "flatarmal": float(flatarmal) if flatarmal else None,
                "fjoldi_herbergja": float(fjoldi) if fjoldi else None,
                "byggingarar": int(byggar) if byggar else None,
                "utgefid": utgefid,
                "thinglyst": thinglyst,
                "address_id": address_id,
            }


def main():
    parser = argparse.ArgumentParser(description="Load HMS kaupskrá data")
    parser.add_argument("--csv", required=True, help="Path to local kaupskra.csv file")
    parser.add_argument(
        "--no-geocode", action="store_true", help="Skip geocoding (fast load)"
    )
    args = parser.parse_args()

    csv_path = args.csv

    os.environ["DATABASE_URL"] = DATABASE_URL
    from planitor.database import db_context
    from sqlalchemy import text

    rows = list(parse_rows(csv_path, geocode=not args.no_geocode))
    logger.info("Parsed %d transactions", len(rows))

    geocoded = sum(1 for r in rows if r["address_id"] is not None)
    logger.info("Geocoded: %d (%.1f%%)", geocoded, 100 * geocoded / len(rows) if rows else 0)

    with db_context() as db:
        db.execute(text("TRUNCATE property_transactions"))
        db.commit()

        batch_size = 5000
        columns = [
            "faerslunumer", "heinum", "fastnum", "heimilisfang", "kaupverd",
            "tegund", "flatarmal", "fjoldi_herbergja", "byggingarar",
            "utgefid", "thinglyst", "address_id",
        ]
        col_list = ", ".join(columns)

        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            value_tuples = []
            for r in batch:
                vals = []
                for col in columns:
                    v = r[col]
                    if v is None:
                        vals.append("NULL")
                    elif isinstance(v, str):
                        vals.append("'" + v.replace("'", "''") + "'")
                    else:
                        vals.append(str(v))
                value_tuples.append("(" + ", ".join(vals) + ")")
            values_sql = ", ".join(value_tuples)
            db.execute(text(f"INSERT INTO property_transactions ({col_list}) VALUES {values_sql}"))
            db.commit()
            logger.info(
                "Inserted batch %d-%d", i + 1, min(i + batch_size, len(rows))
            )

    logger.info("Done. Loaded %d property transactions.", len(rows))


if __name__ == "__main__":
    main()
