"""Geocode property_transactions rows that have no address_id.

Reads ungeocoded rows from DB, geocodes via iceaddr, updates in batches.
Much faster than re-loading the entire CSV.

Usage:
    python scripts/geocode_kaupskra.py
    python scripts/geocode_kaupskra.py --batch-size 10000
"""

import argparse
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


def main():
    parser = argparse.ArgumentParser(description="Geocode property transactions")
    parser.add_argument("--batch-size", type=int, default=5000)
    args = parser.parse_args()

    os.environ["DATABASE_URL"] = DATABASE_URL
    from planitor.database import db_context
    from planitor.geo import get_address_lookup_params, lookup_address
    from sqlalchemy import text

    with db_context() as db:
        # Get all ungeocoded rows
        rows = db.execute(text(
            "SELECT id, heimilisfang FROM property_transactions "
            "WHERE address_id IS NULL AND heimilisfang IS NOT NULL"
        )).fetchall()

        total = len(rows)
        logger.info("Geocoding %d rows ...", total)

        updates = {}  # id -> hnitnum
        geocoded = 0
        failed = 0

        for i, (row_id, heimilisfang) in enumerate(rows):
            try:
                street, number, letter = get_address_lookup_params(heimilisfang)
                if street and number:
                    match = lookup_address(street, number, letter, "")
                    if match:
                        updates[row_id] = match["hnitnum"]
                        geocoded += 1
                    else:
                        failed += 1
                else:
                    failed += 1
            except Exception:
                failed += 1

            # Flush batch
            if len(updates) >= args.batch_size:
                _flush_updates(db, updates)
                logger.info(
                    "Progress: %d/%d (%.1f%%) — geocoded: %d, failed: %d",
                    i + 1, total, 100 * (i + 1) / total, geocoded, failed
                )
                updates = {}

        # Final batch
        if updates:
            _flush_updates(db, updates)

        logger.info(
            "Done. Geocoded: %d, Failed: %d, Total: %d (%.1f%%)",
            geocoded, failed, total, 100 * geocoded / total if total else 0
        )


def _flush_updates(db, updates):
    """Batch UPDATE using a VALUES list + join."""
    from sqlalchemy import text

    if not updates:
        return
    values = ", ".join(f"({row_id}, {hnitnum})" for row_id, hnitnum in updates.items())
    db.execute(text(
        f"UPDATE property_transactions pt SET address_id = v.hnitnum "
        f"FROM (VALUES {values}) AS v(id, hnitnum) "
        f"WHERE pt.id = v.id"
    ))
    db.commit()


if __name__ == "__main__":
    main()
