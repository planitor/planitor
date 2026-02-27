"""Search skatturinn.is company registry to build company_contacts lookup table.

Extracts top unmatched company names from planitor minutes (in their inflected forms
as they appear in text), searches skatturinn.is with multiple strategies, and stores
the exact inflected form → kennitala mapping.

This means the pipeline can match "THG Arkitekta ehf." (genitive) directly without
needing Greynir to normalize to nominative.

Resumable: skips names already in company_contacts or the not-found cache.
Rate-limited: sleeps between requests to avoid blocking.

Usage:
    docker compose exec -T planitor python scripts/search_company_contacts.py
    docker compose exec -T planitor python scripts/search_company_contacts.py --limit 50
    docker compose exec -T planitor python scripts/search_company_contacts.py --delay 5
"""

import argparse
import json
import logging
import re
import sys
import time
from collections import Counter
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

SEARCH_URL = "https://www.skatturinn.is/fyrirtaekjaskra/leit"

# Cache file for names that returned no results (avoid re-searching)
NOT_FOUND_CACHE = Path(__file__).parent / "company_search_not_found.json"

# Company suffixes to strip for search variations
SUFFIXES = ("ehf.", "slhf.", "sf.", "hses.", "hf.", "ohf.", "bs.", "slf.")

RESULT_RE = re.compile(
    r'<a[^>]*href="/fyrirtaekjaskra/leit/kennitala/(\d{10})"[^>]*>\s*(.*?)\s*</a>',
    re.DOTALL,
)
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")

# False positive patterns — not real company names
FALSE_POSITIVE_RE = re.compile(r"^fundargerð", re.IGNORECASE)


def load_not_found_cache():
    if NOT_FOUND_CACHE.exists():
        return set(json.loads(NOT_FOUND_CACHE.read_text()))
    return set()


def save_not_found_cache(cache):
    NOT_FOUND_CACHE.write_text(json.dumps(sorted(cache), ensure_ascii=False, indent=2))


def strip_suffix(name):
    for s in SUFFIXES:
        if name.lower().endswith(" " + s):
            return name[: -(len(s) + 1)].strip()
    return name


def _do_search(session, query, delay):
    """Raw search request. Returns (results, is_redirect).
    results: list of (kennitala, official_name)
    is_redirect: True if skatturinn redirected directly to a company page (high confidence)
    """
    time.sleep(delay)
    try:
        resp = session.get(
            SEARCH_URL,
            params={"nafn": query},
            timeout=30,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "is,en;q=0.5",
            },
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning("  Request failed: %s", e)
        return [], False

    html = resp.text
    if "engri niðurstöðu" in html or "Engin fyrirtæki fundust" in html:
        return [], False

    matches = RESULT_RE.findall(html)
    if matches:
        return [(kt, TAG_RE.sub("", n).strip()) for kt, n in matches], False

    # Landed on company page directly (redirect = high confidence)
    kt_match = re.search(r"/kennitala/(\d{10})", resp.url)
    if kt_match:
        h1_match = H1_RE.search(html)
        name = ""
        if h1_match:
            name = re.sub(r"\s*\(\d{10}\)\s*$", "", TAG_RE.sub("", h1_match.group(1))).strip()
        # If H1 is just the kennitala or empty, use kennitala as placeholder
        if not name or re.match(r"^\d{10}$", name):
            name = kt_match.group(1)
        return [(kt_match.group(1), name)], True

    return [], False


def _guess_word_nominative(word):
    """Generate possible nominative forms for a single inflected Icelandic word."""
    guesses = []
    w = word.lower()
    # Genitive -a → nominative -ar (arkitekta → arkitektar)
    if w.endswith("a"):
        guesses.append(word + "r")
    # Genitive -a → nominative -ir (Félagsbústaða → Félagsbústaðir)
    if w.endswith("a") and len(w) > 3:
        guesses.append(word[:-1] + "ir")
    # Genitive -s → drop (Landslags → Landslag)
    if w.endswith("s") and len(w) > 2:
        guesses.append(word[:-1])
    # Genitive -ar → drop -ar (Hornsteinar → Hornstein)
    if w.endswith("ar") and len(w) > 3:
        guesses.append(word[:-2])
    # Genitive definite -ans → -inn (Meistarans → Meistarinn)
    if w.endswith("ans"):
        guesses.append(word[:-3] + "inn")
    # Genitive definite -ans → -i (Meistarans → Meistari)
    if w.endswith("ans"):
        guesses.append(word[:-3] + "i")
    # Dative -u → nominative -a (teiknistofu → teiknistofa)
    if w.endswith("u"):
        guesses.append(word[:-1] + "a")
    # Genitive -na → -nir / -ur (hafna → hafnir, Veitna → Veitur)
    if w.endswith("na") and len(w) > 3:
        guesses.append(word[:-2] + "nir")
        guesses.append(word[:-2] + "ur")
    # Dative/genitive -unnar → -an (Teiknistofunnar → Teiknistofan)
    if w.endswith("unnar"):
        guesses.append(word[:-5] + "an")
    # Genitive definite -sins → -ið (Batterísins → Batteríið)
    if w.endswith("sins"):
        guesses.append(word[:-4] + "ið")
    # Genitive definite -ins → -ið
    if w.endswith("ins") and not w.endswith("sins"):
        guesses.append(word[:-3] + "ið")
    return guesses


def _guess_nominative_phrases(base):
    """Generate possible nominative forms for a multi-word company name base.

    Applies per-word transforms (especially for the first word and 'arkitekta' pattern),
    plus whole-string transforms for compound patterns.
    """
    guesses = []
    words = base.split()

    # Whole-string transforms (original behavior)
    if base.endswith("a"):
        guesses.append(base + "r")
    if base.endswith("s") and len(base) > 2:
        guesses.append(base[:-1])
    if base.endswith("na"):
        guesses.append(base[:-2] + "nir")
        guesses.append(base[:-2] + "ur")
    if base.endswith("unnar"):
        guesses.append(base[:-5] + "an")
    if " og félaga" in base:
        guesses.append(base.replace(" og félaga", " og félagar"))

    # Per-word transforms: try nominalizing each word individually
    if len(words) >= 2:
        # Transform first word, keep rest
        for nom in _guess_word_nominative(words[0]):
            guesses.append(" ".join([nom] + words[1:]))
        # Transform last word (before suffix was stripped), keep rest
        for nom in _guess_word_nominative(words[-1]):
            guesses.append(" ".join(words[:-1] + [nom]))
        # Transform both first and last word
        for nom1 in _guess_word_nominative(words[0]):
            for nom2 in _guess_word_nominative(words[-1]):
                guesses.append(" ".join([nom1] + words[1:-1] + [nom2]))
    elif len(words) == 1:
        for nom in _guess_word_nominative(words[0]):
            guesses.append(nom)

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for g in guesses:
        if g not in seen and g != base:
            seen.add(g)
            unique.append(g)
    return unique


def _get_suffix(name):
    """Return the company suffix if present, else None."""
    for s in SUFFIXES:
        if name.lower().endswith(" " + s):
            return s
    return None


def _is_company_kennitala(kt):
    """Check if a kennitala belongs to a company (first digit 4-7) vs person (0-3)."""
    return kt[0] in "4567"


def _try_search(session, query, name, delay, trust_redirect=True):
    """Search and pick best match. Returns (kennitala, official_name) or None.
    Redirects from skatturinn are accepted when trust_redirect=True (strategies 1-4).
    For strategy 5 (single-word), use trust_redirect=False to validate word overlap."""
    results, is_redirect = _do_search(session, query, delay)
    if not results:
        return None
    # Filter out person kennitalas
    results = [(kt, n) for kt, n in results if _is_company_kennitala(kt)]
    if not results:
        return None
    if is_redirect and trust_redirect:
        return results[0]
    return _pick_best(results, name)


def search_company(session, name, delay=3.0):
    """Search skatturinn.is with multiple strategies. Returns (kennitala, official_name) or None."""
    suffix = _get_suffix(name)

    # Strategy 1: full name as-is
    match = _try_search(session, name, name, delay)
    if match:
        return match

    # Strategy 2: strip company suffix and search base
    base = strip_suffix(name)
    if base != name:
        match = _try_search(session, base, name, delay)
        if match:
            return match

    # Strategy 3: nominative guesses (per-word and whole-string)
    guesses = _guess_nominative_phrases(base)
    for guess in guesses:
        match = _try_search(session, guess, name, delay)
        if match:
            return match

    # Strategy 4: nominative guesses with suffix re-added
    if suffix:
        for guess in guesses:
            match = _try_search(session, guess + " " + suffix, name, delay)
            if match:
                return match

    # Strategy 5: single distinctive word search (first word of base)
    # Useful for "Mansard teiknistofu ehf." → search "Mansard" → finds "Mansard - Teiknistofa ehf."
    # Use trust_redirect=False — single-word searches are ambiguous, require word overlap
    base_words = base.split()
    if len(base_words) >= 2:
        first_word = base_words[0]
        if len(first_word) >= 3:
            match = _try_search(session, first_word, name, delay, trust_redirect=False)
            if match:
                return match

    return None


def _normalize_for_compare(name):
    """Normalize a company name for comparison: lowercase, strip suffix, remove punctuation."""
    name = strip_suffix(name).lower()
    # Remove common punctuation/separators that vary
    name = name.replace("-", " ").replace("/", " ").replace("–", " ").replace("—", " ")
    return " ".join(name.split())  # normalize whitespace


def _words_similar(a, b):
    """Check if two words are similar enough to count as a match.
    Requires exact match or prefix match where the shorter word is at least
    70% the length of the longer word (avoids 'reita' matching 'reitabolti')."""
    if a == b:
        return True
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    if longer.startswith(shorter) and len(shorter) >= len(longer) * 0.7:
        return True
    return False


def _word_overlap_score(search_words, official_words):
    """Score how many distinctive words overlap between search and official name."""
    skip = {"og", "ehf", "hf", "sf", "bs", "ohf", "slf", "slhf", "hses"}
    s_words = {w for w in search_words if w not in skip and len(w) >= 2}
    o_words = {w for w in official_words if w not in skip and len(w) >= 2}
    if not s_words or not o_words:
        return 0
    matches = 0
    for sw in s_words:
        for ow in o_words:
            if _words_similar(sw, ow):
                matches += 1
                break
    return matches / max(len(s_words), len(o_words))


def _pick_best(results, search_name):
    """Pick the best match from search results. High-confidence only."""
    search_lower = search_name.lower().rstrip(".")
    search_norm = _normalize_for_compare(search_name)
    search_words = search_norm.split()

    # Exact match on full name
    for kt, name in results:
        if name.lower().rstrip(".") == search_lower:
            return (kt, name)

    # Exact match on stripped base
    for kt, name in results:
        official_norm = _normalize_for_compare(name)
        if official_norm == search_norm:
            return (kt, name)

    # High-confidence word overlap: at least 50% of distinctive words must match
    best = None
    best_score = 0
    for kt, name in results:
        official_norm = _normalize_for_compare(name)
        official_words = official_norm.split()
        score = _word_overlap_score(search_words, official_words)
        if score > best_score:
            best_score = score
            best = (kt, name)

    if best and best_score >= 0.5:
        return best

    return None


def get_unmatched_company_names(db):
    """Get regex-matched company names from minutes that don't match existing entities or contacts."""
    from planitor.language.companies import parse_icelandic_companies, clean_company_name
    from planitor.models import Minute, Entity
    from planitor.models.enums import EntityTypeEnum
    from sqlalchemy import func, text

    logger.info("Scanning minutes for company names...")

    batch_size = 1000
    last_id = 0
    all_names = Counter()

    while True:
        minutes = (
            db.query(Minute.id, Minute.inquiry)
            .filter(Minute.inquiry.isnot(None), Minute.inquiry != "", Minute.id > last_id)
            .order_by(Minute.id)
            .limit(batch_size)
            .all()
        )
        if not minutes:
            break
        for mid, inquiry in minutes:
            last_id = mid
            for name in parse_icelandic_companies(inquiry):
                all_names[name] += 1
        db.expunge_all()

    total = sum(all_names.values())
    logger.info("Total company mentions: %d across %d unique forms", total, len(all_names))

    # Filter out already-matched (in entities or company_contacts)
    # Also skip names with inline kennitala prefix — the pipeline handles those directly
    kt_prefix_re = re.compile(r"^\d{6}-?\d{4}\s+")
    unmatched = Counter()
    for name, count in all_names.items():
        if kt_prefix_re.match(name):
            continue
        if FALSE_POSITIVE_RE.match(name):
            continue
        cleaned = clean_company_name(name)
        # Check entities table
        exists = (
            db.query(Entity)
            .filter(
                Entity.entity_type == EntityTypeEnum.company,
                func.lower(Entity.name) == cleaned.lower(),
            )
            .first()
        )
        if exists:
            continue
        # Check company_contacts
        contact = db.execute(
            text("SELECT 1 FROM company_contacts WHERE name = :n"), {"n": name}
        ).first()
        if contact:
            continue
        unmatched[name] = count

    return unmatched, total


def main():
    parser = argparse.ArgumentParser(description="Search skatturinn.is for company kennitalas")
    parser.add_argument("--limit", type=int, default=0, help="Max companies to search")
    parser.add_argument("--delay", type=float, default=3.0, help="Seconds between requests")
    args = parser.parse_args()

    from planitor.database import db_context
    from sqlalchemy import text

    not_found_cache = load_not_found_cache()
    session = requests.Session()

    with db_context() as db:
        existing = set()
        rows = db.execute(text("SELECT name FROM company_contacts")).fetchall()
        for row in rows:
            existing.add(row[0])
        logger.info("Already in company_contacts: %d", len(existing))

        unmatched, total_mentions = get_unmatched_company_names(db)
        unmatched_total = sum(unmatched.values())
        logger.info(
            "Unmatched: %d forms, %d mentions (%d%% of total)",
            len(unmatched),
            unmatched_total,
            unmatched_total * 100 // total_mentions,
        )

        sorted_names = unmatched.most_common()
        searched = 0
        found = 0
        not_found_count = 0
        skipped = 0
        found_mentions = 0

        for name, mention_count in sorted_names:
            if args.limit and searched >= args.limit:
                break

            if name in existing or name in not_found_cache:
                skipped += 1
                continue

            searched += 1
            logger.info("[%d] %s (%d mentions)...", searched, name, mention_count)

            result = search_company(session, name, delay=args.delay)

            if result is None:
                not_found_count += 1
                not_found_cache.add(name)
                logger.info("  NOT FOUND")
            else:
                kt, official_name = result
                found += 1
                found_mentions += mention_count

                # Store the inflected form (as it appears in minutes)
                for store_name in set([name, official_name]):
                    if store_name and store_name not in existing:
                        escaped = store_name.replace("'", "''")
                        try:
                            db.execute(
                                text(
                                    f"INSERT INTO company_contacts (name, kennitala) "
                                    f"VALUES ('{escaped}', '{kt}') "
                                    f"ON CONFLICT (name) DO NOTHING"
                                )
                            )
                            existing.add(store_name)
                        except Exception as e:
                            logger.error("  DB error: %s", e)
                db.commit()
                logger.info("  FOUND: %s -> %s (%s)", name, official_name, kt)

            if searched % 10 == 0:
                save_not_found_cache(not_found_cache)
                coverage = (total_mentions - unmatched_total + found_mentions) * 100 // total_mentions
                logger.info(
                    "-- %d searched, %d found (%d mentions), %d not found | coverage: ~%d%% --",
                    searched, found, found_mentions, not_found_count, coverage,
                )

    save_not_found_cache(not_found_cache)
    logger.info(
        "Done. Searched %d, found %d (%d mentions), not found %d, skipped %d.",
        searched, found, found_mentions, not_found_count, skipped,
    )


if __name__ == "__main__":
    main()
