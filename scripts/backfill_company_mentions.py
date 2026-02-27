"""Fast backfill: re-process entity mentions using regex + company_contacts only (no Greynir).

This is much faster than backfill_person_mentions.py because it skips the Greynir parse
(which takes ~1s per minute). It only handles:
  1. Regex-matched company names → company_contacts lookup
  2. Inline kennitala prefix extraction (e.g., "590269-1749 Skeljungur hf.")

Existing Greynir-based matches are preserved by merging with new matches.

Usage:
    docker compose exec -T planitor python scripts/backfill_company_mentions.py
    docker compose exec -T planitor python scripts/backfill_company_mentions.py --limit 1000
"""

import argparse
import logging
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

BATCH_SIZE = 500
_KT_PREFIX_RE = re.compile(r"^(\d{6})-?(\d{4})\s+")


def main():
    parser = argparse.ArgumentParser(description="Fast backfill company mentions (regex only)")
    parser.add_argument("--limit", type=int, default=0, help="Limit minutes to process")
    parser.add_argument("--offset", type=int, default=0, help="Start from this minute ID")
    args = parser.parse_args()

    from planitor.database import db_context
    from planitor.language.companies import parse_icelandic_companies
    from planitor.models import Minute, CompanyContact
    from planitor.crud.city import get_or_create_entity, get_or_create_case_entity
    from planitor.postprocess import _update_entity_mentions_raw
    from planitor.utils.kennitala import Kennitala
    from sqlalchemy import text
    from sqlalchemy.orm import defer

    processed = 0
    new_entities = 0
    new_mentions = 0
    errors = 0
    last_id = args.offset

    while True:
        with db_context() as db:
            batch = (
                db.query(Minute)
                .options(defer(Minute.entity_mentions))
                .filter(
                    Minute.inquiry.isnot(None),
                    Minute.inquiry != "",
                    Minute.id > last_id,
                )
                .order_by(Minute.id)
                .limit(BATCH_SIZE)
                .all()
            )

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
                        "Limit reached. Processed %d, new entities %d, new mentions %d, errors %d.",
                        processed - 1, new_entities, new_mentions, errors,
                    )
                    return

                try:
                    # Read existing entity_mentions via raw SQL
                    row = db.execute(
                        text("SELECT entity_mentions FROM minutes WHERE id = :id"),
                        {"id": minute.id}
                    ).first()
                    existing_mentions = {}
                    if row and row[0]:
                        # Parse the composite array: each element is (kennitala, start, end_)
                        for item in row[0]:
                            kt = item[0] if isinstance(item, (list, tuple)) else item.entity_id
                            start = item[1] if isinstance(item, (list, tuple)) else item.start
                            end = item[2] if isinstance(item, (list, tuple)) else item.end_
                            if kt not in existing_mentions:
                                existing_mentions[kt] = []
                            existing_mentions[kt].append((start, end))

                    matched_spans = set()
                    for locs in existing_mentions.values():
                        for span in locs:
                            matched_spans.add(span)

                    # Regex company mentions
                    regex_mentions = parse_icelandic_companies(minute.inquiry)
                    added = False

                    for regex_name, locations in regex_mentions.items():
                        new_locations = [loc for loc in locations if loc not in matched_spans]
                        if not new_locations:
                            continue

                        # Check inline kennitala prefix
                        m = _KT_PREFIX_RE.match(regex_name)
                        if m:
                            kt_digits = m.group(1) + m.group(2)
                            company_name = regex_name[m.end():]
                            kennitala = Kennitala(kt_digits)
                            if kennitala.validate():
                                entity, created = get_or_create_entity(
                                    db, kennitala, company_name, address=None
                                )
                                if created:
                                    new_entities += 1
                                    db.commit()
                                get_or_create_case_entity(
                                    db, minute.case, entity, applicant=False
                                )
                                db.commit()
                                if entity.kennitala in existing_mentions:
                                    existing_mentions[entity.kennitala].extend(new_locations)
                                else:
                                    existing_mentions[entity.kennitala] = new_locations
                                for span in new_locations:
                                    matched_spans.add(span)
                                added = True
                                continue

                        # Check company_contacts
                        contact = db.query(CompanyContact).get(regex_name)
                        if contact is None:
                            continue
                        kennitala = Kennitala(contact.kennitala)
                        if not kennitala.validate():
                            continue
                        entity, created = get_or_create_entity(
                            db, kennitala, regex_name, address=None
                        )
                        if created:
                            new_entities += 1
                            db.commit()
                        get_or_create_case_entity(
                            db, minute.case, entity, applicant=False
                        )
                        db.commit()
                        if entity.kennitala in existing_mentions:
                            existing_mentions[entity.kennitala].extend(new_locations)
                        else:
                            existing_mentions[entity.kennitala] = new_locations
                        for span in new_locations:
                            matched_spans.add(span)
                        added = True

                    if added:
                        _update_entity_mentions_raw(db, minute.id, existing_mentions)
                        new_mentions += 1

                except Exception as e:
                    errors += 1
                    if errors <= 10:
                        logger.error("Error on minute %d: %s", minute.id, e)

                if processed % 1000 == 0:
                    logger.info(
                        "Progress: %d processed, %d new mentions, %d new entities, %d errors (last_id=%d)",
                        processed, new_mentions, new_entities, errors, last_id,
                    )

            db.expunge_all()

    logger.info(
        "Done. Processed %d, new mentions %d, new entities %d, errors %d.",
        processed, new_mentions, new_entities, errors,
    )


if __name__ == "__main__":
    main()
