"""Import person contacts from contacts.csv into the person_contacts table.

Reads ~/contacts.csv, filters to rows with kennitala, deduplicates by name
(skips ambiguous names with multiple kennitalas), and bulk inserts.

Usage:
    python scripts/import_person_contacts.py
    python scripts/import_person_contacts.py --csv ~/contacts.csv
"""

import argparse
import csv
import logging
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://planitor:password@localhost:5432/planitor"
)


def main():
    parser = argparse.ArgumentParser(description="Import person contacts from CSV")
    parser.add_argument(
        "--csv",
        default=os.path.expanduser("~/contacts.csv"),
        help="Path to contacts CSV file",
    )
    args = parser.parse_args()

    # Read CSV and group by name
    name_to_kennitalas = defaultdict(set)
    total_rows = 0
    rows_with_kt = 0

    with open(args.csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_rows += 1
            kennitala = row.get("kennitala", "").strip()
            name = row.get("name", "").strip()
            if not kennitala or not name:
                continue
            rows_with_kt += 1
            name_to_kennitalas[name].add(kennitala)

    # Filter to unambiguous names (single kennitala)
    unique_contacts = {}
    ambiguous = 0
    for name, kennitalas in name_to_kennitalas.items():
        if len(kennitalas) == 1:
            unique_contacts[name] = kennitalas.pop()
        else:
            ambiguous += 1

    logger.info("Total CSV rows: %d", total_rows)
    logger.info("Rows with kennitala: %d", rows_with_kt)
    logger.info("Unique names: %d", len(name_to_kennitalas))
    logger.info("Ambiguous names (skipped): %d", ambiguous)
    logger.info("Contacts to import: %d", len(unique_contacts))

    # Import into database
    os.environ["DATABASE_URL"] = DATABASE_URL
    from planitor.database import db_context
    from sqlalchemy import text

    with db_context() as db:
        # Truncate existing data
        db.execute(text("TRUNCATE person_contacts"))
        db.commit()

        # Bulk insert in batches
        batch_size = 5000
        items = list(unique_contacts.items())
        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            values = ", ".join(
                f"('{name.replace(chr(39), chr(39)+chr(39))}', '{kt}')"
                for name, kt in batch
            )
            db.execute(
                text(f"INSERT INTO person_contacts (name, kennitala) VALUES {values}")
            )
            db.commit()
            logger.info("Inserted batch %d-%d", i + 1, min(i + batch_size, len(items)))

    logger.info("Done. Imported %d person contacts.", len(unique_contacts))


if __name__ == "__main__":
    main()
