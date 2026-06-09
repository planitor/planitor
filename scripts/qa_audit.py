"""
QA Audit Script — Run via: docker compose exec -T planitor python < scripts/qa_audit.py

Compares source data quality across all NLP/processing features.
Auto-selects 2 recent meetings per council type (4 total).
"""

from hashids import Hashids
from sqlalchemy import func, text

from planitor.database import SessionLocal
from planitor.models import Meeting, Minute

h = Hashids(salt="planitor", min_length=4)
session = SessionLocal()

# --- Step 0: Auto-select sample meetings ---
print("=" * 70)
print("STEP 0: SAMPLE MEETINGS")
print("=" * 70)

meeting_ids = []
for council_id, name in [(3, "byggingarfulltrui"), (4, "skipulagsfulltrui")]:
    results = (
        session.query(Meeting, func.count(Minute.id))
        .outerjoin(Minute)
        .filter(Meeting.council_id == council_id)
        .group_by(Meeting.id)
        .order_by(Meeting.start.desc())
        .limit(5)
        .all()
    )
    # Pick 1st (most recent) and 3rd (slightly older)
    picks = [results[0], results[min(2, len(results) - 1)]]
    for m, count in picks:
        meeting_ids.append(m.id)
        print(
            f"  {name}: meeting {m.name} id={m.id} hash={h.encode(m.id)} "
            f"start={m.start} minutes={count}"
        )
        print(f"    source: {m.url}")
        if "fundargerdir" in (m.url or ""):
            print(
                f"    planitor: https://www.planitor.io/s/reykjavik/{name}/fundir/{h.encode(m.id)}"
            )
        else:
            print(
                f"    planitor: https://www.planitor.io/s/reykjavik/{name}/fundir/{h.encode(m.id)}"
            )

# --- Step 1: Item Counts ---
print("\n" + "=" * 70)
print("STEP 1: ITEM COUNTS")
print("=" * 70)
for mid in meeting_ids:
    count = (
        session.query(func.count(Minute.id)).filter(Minute.meeting_id == mid).scalar()
    )
    m = session.query(Meeting).get(mid)
    print(f"  Meeting {m.name} (id={mid}): {count} minutes")

# --- Step 2: Status Detection ---
print("\n" + "=" * 70)
print("STEP 2: NULL STATUS WITH NON-EMPTY REMARKS")
print("=" * 70)
for mid in meeting_ids:
    m = session.query(Meeting).get(mid)
    results = session.execute(
        text(
            "SELECT min.serial, c.serial, min.status, LEFT(min.remarks, 150) "
            "FROM minutes min JOIN cases c ON min.case_id = c.id "
            "WHERE min.meeting_id = :mid AND min.status IS NULL "
            "AND min.remarks IS NOT NULL AND min.remarks != ''"
        ),
        {"mid": mid},
    ).fetchall()
    print(f"\n  Meeting {m.name} (id={mid}): {len(results)} null-status items")
    for r in results:
        print(f"    serial={r[0]} case={r[1]} remarks={r[3]!r}")

# --- Step 3: Geocoding Failures ---
print("\n" + "=" * 70)
print("STEP 3: GEOCODING FAILURES")
print("=" * 70)
for mid in meeting_ids:
    m = session.query(Meeting).get(mid)
    failures = session.execute(
        text(
            "SELECT c.serial, c.address, LEFT(min.headline, 80) "
            "FROM minutes min JOIN cases c ON min.case_id = c.id "
            "WHERE min.meeting_id = :mid AND c.address_id IS NULL"
        ),
        {"mid": mid},
    ).fetchall()
    total = session.execute(
        text("SELECT COUNT(*) FROM minutes WHERE meeting_id = :mid"), {"mid": mid}
    ).scalar()
    geocoded = total - len(failures)
    pct = 100 * geocoded / total if total else 0
    print(f"\n  Meeting {m.name} (id={mid}): {geocoded}/{total} geocoded ({pct:.0f}%)")
    for r in failures[:8]:
        print(f"    FAIL case={r[0]} address={r[1]!r} headline={r[2]!r}")
    if len(failures) > 8:
        print(f"    ... and {len(failures) - 8} more")

# --- Step 4: Inquiry/Remarks Split ---
print("\n" + "=" * 70)
print("STEP 4: INQUIRY/REMARKS SPLIT QUALITY")
print("=" * 70)
for mid in meeting_ids:
    m = session.query(Meeting).get(mid)
    # Decision text leaked into inquiry
    leaked = session.execute(
        text(
            "SELECT min.serial, c.serial, LEFT(min.inquiry, 150) "
            "FROM minutes min JOIN cases c ON min.case_id = c.id "
            "WHERE min.meeting_id = :mid "
            "AND (min.remarks IS NULL OR min.remarks = '') "
            "AND (min.inquiry LIKE '%Samþykkt%' OR min.inquiry LIKE '%Frestað%' "
            "     OR min.inquiry LIKE '%Synjað%' OR min.inquiry LIKE '%Vísað til%')"
        ),
        {"mid": mid},
    ).fetchall()
    # Fylgigögn contamination
    fylgi = session.execute(
        text(
            "SELECT min.serial FROM minutes min "
            "WHERE min.meeting_id = :mid AND min.remarks LIKE '%Fylgigögn%'"
        ),
        {"mid": mid},
    ).fetchall()
    print(
        f"  Meeting {m.name}: {len(leaked)} split failures, {len(fylgi)} Fylgigögn leaks"
    )
    for r in leaked:
        print(f"    LEAK serial={r[0]} case={r[1]} inquiry={r[2]!r}")

# --- Step 5: Search Vectors ---
print("\n" + "=" * 70)
print("STEP 5: SEARCH VECTOR COVERAGE")
print("=" * 70)
for mid in meeting_ids:
    m = session.query(Meeting).get(mid)
    result = session.execute(
        text(
            "SELECT COUNT(*) AS total, COUNT(search_vector) AS indexed "
            "FROM minutes WHERE meeting_id = :mid"
        ),
        {"mid": mid},
    ).fetchone()
    missing = result[0] - result[1]
    status = "OK" if missing == 0 else f"MISSING {missing}"
    print(f"  Meeting {m.name}: {result[1]}/{result[0]} indexed [{status}]")

# --- Step 6: Entity Mentions ---
print("\n" + "=" * 70)
print("STEP 6: ENTITY EXTRACTION")
print("=" * 70)
for mid in meeting_ids:
    m = session.query(Meeting).get(mid)
    with_suffix = session.execute(
        text(
            "SELECT COUNT(*) FROM minutes min JOIN cases c ON min.case_id = c.id "
            "WHERE min.meeting_id = :mid "
            "AND (min.inquiry LIKE '%% ehf.%%' OR min.inquiry LIKE '%% hf.%%' "
            "     OR min.inquiry LIKE '%% ohf.%%' OR min.inquiry LIKE '%% slf.%%')"
        ),
        {"mid": mid},
    ).scalar()
    with_mentions = session.execute(
        text(
            "SELECT COUNT(DISTINCT min.id) FROM minutes min "
            "JOIN minute_entity_mentions mem ON mem.minute_id = min.id "
            "WHERE min.meeting_id = :mid"
        ),
        {"mid": mid},
    ).scalar()
    print(
        f"  Meeting {m.name}: {with_mentions} entity_mentions / "
        f"{with_suffix} items with company suffixes"
    )

# --- Step 7: Attachments ---
print("\n" + "=" * 70)
print("STEP 7: ATTACHMENTS")
print("=" * 70)
for mid in meeting_ids:
    m = session.query(Meeting).get(mid)
    result = session.execute(
        text(
            "SELECT COUNT(DISTINCT min.id) AS items, COUNT(att.id) AS atts "
            "FROM minutes min LEFT JOIN attachments att ON att.minute_id = min.id "
            "WHERE min.meeting_id = :mid"
        ),
        {"mid": mid},
    ).fetchone()
    print(f"  Meeting {m.name}: {result[1]} attachments across {result[0]} items")

# --- Aggregate Stats ---
print("\n" + "=" * 70)
print("AGGREGATE RATES (Reykjavik)")
print("=" * 70)

print("\n  Status Detection:")
results = session.execute(
    text(
        "SELECT c.council_type, COUNT(min.id), COUNT(min.status), "
        "ROUND(100.0 * COUNT(min.status) / NULLIF(COUNT(min.id), 0), 1) "
        "FROM minutes min JOIN meetings m ON min.meeting_id = m.id "
        "JOIN councils c ON m.council_id = c.id "
        "WHERE c.municipality_id = 0 GROUP BY c.council_type"
    )
).fetchall()
for r in results:
    print(f"    {r[0]}: {r[2]}/{r[1]} ({r[3]}%)")

print("\n  Geocoding:")
results = session.execute(
    text(
        "SELECT c.council_type, COUNT(DISTINCT cs.id), "
        "COUNT(DISTINCT CASE WHEN cs.address_id IS NOT NULL THEN cs.id END), "
        "ROUND(100.0 * COUNT(DISTINCT CASE WHEN cs.address_id IS NOT NULL THEN cs.id END) "
        "/ NULLIF(COUNT(DISTINCT cs.id), 0), 1) "
        "FROM cases cs JOIN minutes min ON min.case_id = cs.id "
        "JOIN meetings m ON min.meeting_id = m.id "
        "JOIN councils c ON m.council_id = c.id "
        "WHERE cs.municipality_id = 0 GROUP BY c.council_type"
    )
).fetchall()
for r in results:
    print(f"    {r[0]}: {r[2]}/{r[1]} ({r[3]}%)")

print("\n  Status Value Distribution:")
results = session.execute(
    text(
        "SELECT COALESCE(min.status::text, '(none)'), COUNT(*) FROM minutes min "
        "JOIN meetings m ON min.meeting_id = m.id "
        "JOIN councils c ON m.council_id = c.id "
        "WHERE c.municipality_id = 0 "
        "GROUP BY min.status ORDER BY COUNT(*) DESC"
    )
).fetchall()
for r in results:
    print(f"    {r[0]}: {r[1]}")

session.close()
print("\n" + "=" * 70)
print("AUDIT COMPLETE")
print("=" * 70)
