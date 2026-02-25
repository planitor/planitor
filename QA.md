# QA Harness — Repeatable Code Agent Workflow

A rinse-and-repeat playbook for a code agent to verify planitor data quality. The cycle: sample meetings from the database, inspect the original source, compare against planitor.io and DB records feature-by-feature, fix mismatches, and repeat. No issue tracking here — fixes belong in git commits and memory files.

---

## The QA Cycle

### Phase 1 — Sample

Pick **2 recent meetings per active spider** plus **1 skipulagsrad meeting** (historical, no active spider). The audit script auto-selects good candidates:

```bash
docker compose exec -T planitor python < scripts/qa_audit.py
```

Or manually query:

```sql
-- Recent meetings with minute counts (adjust council_id: 3=byggingarfulltrui, 4=skipulagsfulltrui, 5=skipulagsrad)
SELECT m.id, m.name, m.start, m.url, COUNT(min.id) AS items
FROM meetings m LEFT JOIN minutes min ON min.meeting_id = m.id
WHERE m.council_id = 4
GROUP BY m.id ORDER BY m.start DESC LIMIT 5;
```

For each sampled meeting, record:
- **Meeting ID** and **hashid** (for planitor.io URLs): `python -c "from hashids import Hashids; print(Hashids(salt='planitor', min_length=4).encode(MEETING_ID))"`
- **Source URL** (from `m.url`)
- **Planitor.io URL**: `https://www.planitor.io/s/reykjavik/{council}/fundir/{hashid}`

### Phase 2 — Inspect Source

**HTML meetings** (skipulagsfulltrui_html): WebFetch the source URL and extract:
- Total agenda item count
- Per item: serial (Mál nr.), address, headline, decision/remarks text

**PDF meetings** (byggingarfulltrui_pdf): Cannot WebFetch PDFs directly. Instead:
- Note the source URL for manual verification
- Rely on DB item count and the audit script output

Record findings per meeting: item count, case serials, addresses, decision text.

### Phase 3 — Compare Against Planitor.io

For each sampled meeting, check every feature systematically:

| Feature | What to check | Source of truth | Planitor.io page | DB query |
|---------|--------------|-----------------|-------------------|----------|
| **Completeness** | All agenda items captured? | Source item count | Meeting page item count | `SELECT COUNT(*) FROM minutes WHERE meeting_id = X` |
| **Case serials** | Correct USK/SN/BN/US numbers? | Source "Mál nr." text | Case links on meeting page | `SELECT c.serial FROM minutes min JOIN cases c ON min.case_id = c.id WHERE min.meeting_id = X` |
| **Headlines** | Clean text, no "Mál nr." suffix or `\xa0`? | Source headline | Meeting page item titles | `SELECT min.headline FROM minutes WHERE meeting_id = X` |
| **Status detection** | Remarks mapped to correct status? | Source decision paragraph | Status pill color/text | `SELECT min.serial, min.status, LEFT(min.remarks, 150) FROM minutes min WHERE meeting_id = X AND status IS NULL AND remarks != ''` |
| **Address extraction** | Street + number parsed from headline? | Source headline | Address shown on case page | `SELECT c.serial, c.address, c.address_id FROM minutes min JOIN cases c ON min.case_id = c.id WHERE min.meeting_id = X AND c.address_id IS NULL` |
| **Geocoding** | Address resolved to map coordinates? | Known street address | Map pin on `/s/{muni}/nr/{serial}` | `SELECT c.serial, c.address FROM minutes min JOIN cases c ON min.case_id = c.id WHERE min.meeting_id = X AND c.address_id IS NULL` |
| **Inquiry/remarks split** | Clean separation? No decision text in inquiry, no Fylgigogn in remarks? | Source full text | Minute detail page | `SELECT min.serial, LEFT(min.inquiry, 100), LEFT(min.remarks, 100) FROM minutes min WHERE meeting_id = X AND (remarks LIKE '%Fylgig%' OR (remarks = '' AND inquiry LIKE '%Samþykkt%'))` |
| **Search indexing** | search_vector populated? | N/A | Search `/leit?q=...` returns item | `SELECT COUNT(*) - COUNT(search_vector) AS missing FROM minutes WHERE meeting_id = X` |
| **Entity linking** | Company names in inquiry hyperlinked? | Source text with ehf./hf. | Entity links on minute page | `SELECT min.serial, min.entity_mentions FROM minutes min WHERE meeting_id = X AND inquiry LIKE '% ehf.%'` |
| **Attachments** | Document links captured? | Source page links | Minute detail attachments | `SELECT min.serial, COUNT(att.id) FROM minutes min LEFT JOIN attachments att ON att.minute_id = min.id WHERE min.meeting_id = X GROUP BY min.serial` |
| **Case timeline** | Multiple minutes from different meetings on case page? | Cross-reference meetings | Case page `/s/{muni}/nr/{serial}` | `SELECT min.meeting_id, m.name FROM minutes min JOIN meetings m ON min.meeting_id = m.id WHERE min.case_id = (SELECT case_id FROM minutes WHERE meeting_id = X LIMIT 1)` |
| **Address page** | Related cases at same address shown? | N/A | Address page `/heimilisfong/{hnitnum}` | `SELECT cs.serial, cs.address FROM cases cs WHERE cs.address_id = (SELECT c.address_id FROM minutes min JOIN cases c ON min.case_id = c.id WHERE min.meeting_id = X AND c.address_id IS NOT NULL LIMIT 1)` |

### Phase 4 — Fix & Verify

For each mismatch found in Phase 3:

1. **Identify** the responsible file/function (see Key Files below)
2. **Make the code fix**
3. **Rebuild**:
   ```bash
   cd ~/mediaserver && docker compose up -d --build planitor
   ```
4. **Re-scrape** affected meetings — must delete dependents first:
   ```sql
   -- Delete cascade for a meeting (order matters: deliveries → attachments → minutes)
   DELETE FROM deliveries WHERE minute_id IN (SELECT id FROM minutes WHERE meeting_id = X);
   DELETE FROM attachments WHERE minute_id IN (SELECT id FROM minutes WHERE meeting_id = X);
   DELETE FROM minutes WHERE meeting_id = X;
   ```
   Then run the spider:
   ```bash
   docker compose exec -T planitor scrapy crawl reykjavik_skipulagsfulltrui_html -a limit=5
   ```
5. **Re-check** — repeat Phase 3 queries on the fixed meetings
6. **Regression check** — run the full audit script:
   ```bash
   docker compose exec -T planitor python < scripts/qa_audit.py
   ```

---

## Tools Reference

| Task | Command |
|------|---------|
| Run audit script | `docker compose exec -T planitor python < scripts/qa_audit.py` |
| Run arbitrary Python | `docker compose exec -T planitor python -c "..."` |
| Inspect HTML source | WebFetch on `reykjavik.is` meeting URL |
| Inspect planitor.io | WebFetch on `www.planitor.io` meeting/case URL |
| Run spider (limited) | `docker compose exec -T planitor scrapy crawl SPIDER -a limit=N` |
| Rebuild container | `cd ~/mediaserver && docker compose up -d --build planitor` |
| Direct DB query | `docker compose exec -T planitor python -c "from planitor.database import SessionLocal; db = SessionLocal(); print(db.execute(...).fetchall())"` |

---

## Feature Test Recipes

Test each enrichment feature in isolation inside the container:

**Status detection**
```bash
docker compose exec -T planitor python -c "
from planitor.cases import get_case_status_from_remarks
print(get_case_status_from_remarks('Samþykkt.'))
print(get_case_status_from_remarks('Frestað.'))
print(get_case_status_from_remarks('YOUR TEST STRING'))
"
```

**Geocoding**
```bash
docker compose exec -T planitor python -c "
from planitor.geo import get_address_lookup_params, lookup_address
street, num, letter = get_address_lookup_params('Laugavegur 12')
print(f'{street=} {num=} {letter=}')
print(lookup_address(street, num, letter, 'Reykjavík'))
"
```

**Lemmatization**
```bash
curl -s 'https://lemma.solberg.is/api/text' \
  -H 'Content-Type: application/json' \
  -d '{"text": "Samþykkt að gefa út framkvæmdaleyfi"}' | python -m json.tool
```

**Search query**
```bash
docker compose exec -T planitor python -c "
from sqlalchemy import text
from planitor.database import SessionLocal
db = SessionLocal()
rows = db.execute(text(\"\"\"
  SELECT min.id, c.serial, c.address, ts_rank(min.search_vector, q) AS rank
  FROM minutes min JOIN cases c ON min.case_id = c.id,
       plainto_tsquery('simple', 'framkvæmdaleyfi') q
  WHERE min.search_vector @@ q ORDER BY rank DESC LIMIT 5
\"\"\")).fetchall()
for r in rows: print(r)
"
```

**Entity extraction check**
```bash
docker compose exec -T planitor python -c "
from sqlalchemy import text
from planitor.database import SessionLocal
db = SessionLocal()
rows = db.execute(text(\"\"\"
  SELECT min.serial, min.entity_mentions, LEFT(min.inquiry, 80)
  FROM minutes min WHERE min.inquiry LIKE '%% ehf.%%'
  AND min.entity_mentions IS NOT NULL ORDER BY min.id DESC LIMIT 5
\"\"\")).fetchall()
for r in rows: print(r)
"
```

---

## Key Files

| Feature | File | Function |
|---------|------|----------|
| Status detection | `planitor/cases.py:111` | `get_case_status_from_remarks()` |
| Address parsing | `planitor/geo.py:18` | `get_address_lookup_params()` |
| Address geocoding | `planitor/geo.py:57` | `lookup_address()` |
| Case creation | `planitor/crud/city.py:122` | `get_or_create_case()` |
| Minute creation + geocode | `planitor/crud/city.py:166` | `create_minute()` |
| Minute postprocessing | `planitor/postprocess.py:254` | `process_minutes()` |
| Search vector indexing | `planitor/postprocess.py:178` | `_update_minute_search_vector()` |
| Entity mentions | `planitor/postprocess.py:73` | `_update_entity_mentions_raw()` |
| Scrape pipeline | `scrape/pipelines.py:47` | `DatabasePipeline.process_item()` |
| HTML spider | `scrape/spiders/reykjavik_skipulagsfulltrui_html.py` | `parse_meeting()` |
| PDF spider | `scrape/spiders/reykjavik_byggingarfulltrui_pdf.py` | `parse_pdf()` |
