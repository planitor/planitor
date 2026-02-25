"""Re-run entity mention extraction on all minutes to pick up person mentions.

This re-runs _update_minute_with_entity_mentions() which now handles both
company and person name extraction. It's idempotent — it overwrites the
entity_mentions array each time.

Usage:
    docker compose exec -T planitor python scripts/backfill_person_mentions.py
    docker compose exec -T planitor python scripts/backfill_person_mentions.py --limit 100
"""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

BATCH_SIZE = 100


def main():
    parser = argparse.ArgumentParser(
        description="Backfill person entity mentions on minutes"
    )
    parser.add_argument(
        "--limit", type=int, default=0, help="Limit number of minutes to process"
    )
    parser.add_argument(
        "--offset", type=int, default=0, help="Start from this minute ID"
    )
    args = parser.parse_args()

    from planitor.database import db_context
    from planitor.models import Minute
    from planitor.postprocess import _update_minute_with_entity_mentions
    from sqlalchemy.orm import defer

    processed = 0
    errors = 0
    updated = 0
    last_id = args.offset

    while True:
        with db_context() as db:
            query = (
                db.query(Minute)
                .options(defer(Minute.entity_mentions))
                .filter(
                    Minute.inquiry.isnot(None),
                    Minute.inquiry != "",
                    Minute.id > last_id,
                )
                .order_by(Minute.id)
                .limit(BATCH_SIZE)
            )
            batch = query.all()

            if not batch:
                break

            if processed == 0 and args.offset == 0:
                total = (
                    db.query(Minute)
                    .filter(Minute.inquiry.isnot(None), Minute.inquiry != "")
                    .count()
                )
                logger.info("Total minutes with inquiry text: %d", total)

            for minute in batch:
                last_id = minute.id
                processed += 1

                if args.limit and processed > args.limit:
                    logger.info(
                        "Limit reached. Processed %d, updated %d, errors %d.",
                        processed - 1,
                        updated,
                        errors,
                    )
                    return

                try:
                    _update_minute_with_entity_mentions(db, minute)
                    updated += 1
                except Exception as e:
                    errors += 1
                    logger.error("Error on minute %d: %s", minute.id, e)

                if processed % 100 == 0:
                    logger.info(
                        "Progress: %d processed, %d updated, %d errors (last_id=%d)",
                        processed,
                        updated,
                        errors,
                        last_id,
                    )

            db.expunge_all()

    logger.info(
        "Done. Processed %d, updated %d, errors %d.", processed, updated, errors
    )


if __name__ == "__main__":
    main()
