"""Fix skipulagsrad F-prefix case serials by extracting real serial from headline.

239 items across 11 meetings (Jan-May 2022) have synthetic F{meeting}-{serial}
case serials, but 227 have the real serial embedded as "Mál nr. SN210221" in
the headline text.

Run: docker compose exec -T planitor python < scripts/fix_skipulagsrad_serials.py
"""
import re
import sys

from sqlalchemy import text

from planitor.database import SessionLocal

# Reuse the proven parser from the skipulagsrad spider
CASE_SERIAL_RE = re.compile(r"Mál nr\. ((?:[A-Z]{2,3})\d+)")


def parse_headline(headline):
    """Extract case serial from headline and return cleaned headline + serial."""
    serial = None
    match = CASE_SERIAL_RE.search(headline)
    if match:
        serial = match.group(1)
        headline = CASE_SERIAL_RE.sub("", headline)

    # Clean up stadgreinir like (04.071)
    headline = re.sub(r"\([\d\.]{2,}\)", "", headline)
    # Normalize whitespace and \xa0
    headline = re.sub(r" +", " ", headline.replace("\xa0", " ")).strip()
    # Strip trailing comma/period
    headline = headline.rstrip(",").rstrip(".").strip()

    return headline, serial


def main():
    import os
    dry_run = os.environ.get("DRY_RUN", "1") == "1"

    session = SessionLocal()

    # Find all F-prefix minutes in skipulagsrad
    rows = session.execute(text("""
        SELECT min.id, min.serial, min.headline, c.id as case_id, c.serial as case_serial,
               m.name as meeting_name
        FROM minutes min
        JOIN cases c ON min.case_id = c.id
        JOIN meetings m ON min.meeting_id = m.id
        WHERE m.council_id = 5 AND c.serial LIKE 'F%%'
        ORDER BY m.start, min.serial
    """)).fetchall()

    print(f"Found {len(rows)} F-prefix items in skipulagsrad")

    fixed = 0
    unfixable = 0
    merged = 0

    for row in rows:
        min_id, min_serial, headline, case_id, old_case_serial, meeting_name = row
        clean_headline, extracted_serial = parse_headline(headline)

        if not extracted_serial:
            unfixable += 1
            print(f"  SKIP min={min_id} case={old_case_serial}: no serial in headline")
            continue

        # Check if a case with this serial already exists
        existing = session.execute(text(
            "SELECT id FROM cases WHERE serial = :serial AND municipality_id = 0"
        ), {"serial": extracted_serial}).fetchone()

        if existing:
            existing_case_id = existing[0]
            if existing_case_id != case_id:
                # Re-point minute to the existing case, then delete orphan
                if not dry_run:
                    session.execute(text(
                        "UPDATE minutes SET case_id = :new_case_id, headline = :headline "
                        "WHERE id = :min_id"
                    ), {"new_case_id": existing_case_id, "headline": clean_headline,
                        "min_id": min_id})
                    # Check if old case has other minutes
                    other = session.execute(text(
                        "SELECT COUNT(*) FROM minutes WHERE case_id = :cid AND id != :mid"
                    ), {"cid": case_id, "mid": min_id}).scalar()
                    if other == 0:
                        # Delete orphaned case_entities first
                        session.execute(text(
                            "DELETE FROM case_entities WHERE case_id = :cid"
                        ), {"cid": case_id})
                        session.execute(text(
                            "DELETE FROM cases WHERE id = :cid"
                        ), {"cid": case_id})
                merged += 1
                print(f"  MERGE min={min_id} {old_case_serial} -> existing case {extracted_serial} (id={existing_case_id})")
                print(f"    headline: {clean_headline[:80]}")
            else:
                # Already pointing to right case, just fix serial and headline
                if not dry_run:
                    session.execute(text(
                        "UPDATE cases SET serial = :serial WHERE id = :cid"
                    ), {"serial": extracted_serial, "cid": case_id})
                    session.execute(text(
                        "UPDATE minutes SET headline = :headline WHERE id = :min_id"
                    ), {"headline": clean_headline, "min_id": min_id})
                fixed += 1
                print(f"  FIX  min={min_id} {old_case_serial} -> {extracted_serial}")
        else:
            # No existing case — rename the F-prefix case
            if not dry_run:
                session.execute(text(
                    "UPDATE cases SET serial = :serial WHERE id = :cid"
                ), {"serial": extracted_serial, "cid": case_id})
                session.execute(text(
                    "UPDATE minutes SET headline = :headline WHERE id = :min_id"
                ), {"headline": clean_headline, "min_id": min_id})
            fixed += 1
            print(f"  FIX  min={min_id} {old_case_serial} -> {extracted_serial}")
            print(f"    headline: {clean_headline[:80]}")

    if not dry_run:
        session.commit()

    print(f"\nSummary: {fixed} fixed, {merged} merged, {unfixable} unfixable")
    if dry_run:
        print("(DRY RUN — no changes made)")
    session.close()


if __name__ == "__main__":
    main()
