"""Download and render deiliskipulag PDFs to JPEG page images in MinIO.

Rendering priority:
- skipulagsuppdráttur: ALL pages (zoning maps, 1-3 pages, highest visual value)
- greinargerð: FIRST PAGE only (cover preview)
- skýringaruppdráttur: SKIP (redundant, huge files 28+ MB)

Each PDF is rendered in a child process to isolate pypdfium2 memory.
Full PDFs are discarded after rendering — only page JPEGs are stored.

Page key pattern: deiliskipulag-{skipnr}-{type_short}-page-{i}.jpg
  type_short: gr (greinargerð), up (uppdráttur), sk (skýringaruppdráttur)

Usage:
    docker compose exec -T planitor python scripts/render_deiliskipulag_pdfs.py
    docker compose exec -T planitor python scripts/render_deiliskipulag_pdfs.py --limit 10
    docker compose exec -T planitor python scripts/render_deiliskipulag_pdfs.py --dry-run
"""

import argparse
import datetime as dt
import logging
import multiprocessing
import sys
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

BATCH_SIZE = 50

DOC_TYPE_SHORT = {
    "greinargerð": "gr",
    "uppdráttur": "up",
    "skýringaruppdráttur": "sk",
}

# Max pages to render per doc type
MAX_PAGES = {
    "uppdráttur": None,  # All pages
    "greinargerð": 1,  # First page only
}

# Only render these doc types (skip everything else)
RENDER_DOC_TYPES = {"uppdráttur", "greinargerð"}

# Max file size to download (MB) — skip huge files
MAX_FILE_SIZE_MB = 50


def _render_worker(skipnr, doc_type, source_url, max_pages, page_count_val):
    """Run in child process. Downloads PDF, renders pages, uploads to MinIO.

    page_count_val is a multiprocessing.Value('i') for returning the rendered count.
    """
    import pypdfium2
    from PIL import Image

    from planitor.attachments import minio, MINIO_PAGES_BUCKET

    type_short = DOC_TYPE_SHORT.get(doc_type, doc_type[:2])
    key_prefix = f"deiliskipulag-{skipnr}-{type_short}"

    req = Request(source_url, headers={"User-Agent": "planitor/1.0"})
    try:
        with urlopen(req, timeout=120) as response:
            pdf_bytes = response.read()
    except (HTTPError, URLError, TimeoutError) as e:
        logging.getLogger(__name__).error("Download failed: %s", e)
        sys.exit(1)

    pdf = pypdfium2.PdfDocument(pdf_bytes)
    total_pages = len(pdf)
    render_count = min(total_pages, max_pages) if max_pages else total_pages

    for i in range(render_count):
        page = pdf[i]
        scale = 1500 / page.get_width()
        bitmap = page.render(scale=scale)
        pil_image = bitmap.to_pil()
        bitmap.close()
        page.close()

        if pil_image.mode != "RGB":
            rgb = pil_image.convert("RGB")
            pil_image.close()
            pil_image = rgb

        buf = BytesIO()
        pil_image.save(buf, format="JPEG", quality=85)
        pil_image.close()
        buf.seek(0)

        key = f"{key_prefix}-page-{i}.jpg"
        minio.upload_fileobj(
            buf,
            MINIO_PAGES_BUCKET,
            key,
            ExtraArgs={"ContentType": "image/jpeg"},
        )
        buf.close()

    pdf.close()
    page_count_val.value = render_count


def main():
    parser = argparse.ArgumentParser(description="Render deiliskipulag PDFs to JPEG")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of documents to render")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be rendered")
    parser.add_argument(
        "--timeout", type=int, default=300, help="Timeout per PDF in seconds (default: 300)"
    )
    args = parser.parse_args()

    from planitor.database import db_context
    from planitor.models import DeiliskipulagDocument

    with db_context() as db:
        total = (
            db.query(DeiliskipulagDocument)
            .filter(
                DeiliskipulagDocument.pages_rendered_at.is_(None),
                DeiliskipulagDocument.doc_type.in_(RENDER_DOC_TYPES),
            )
            .count()
        )
        logger.info("Unrendered documents (excl. skýringaruppdráttur): %d", total)

        if args.dry_run:
            docs = (
                db.query(DeiliskipulagDocument)
                .filter(
                    DeiliskipulagDocument.pages_rendered_at.is_(None),
                    DeiliskipulagDocument.doc_type.in_(RENDER_DOC_TYPES),
                )
                .order_by(DeiliskipulagDocument.skipnr)
                .limit(20)
                .all()
            )
            for doc in docs:
                logger.info(
                    "  [dry-run] skipnr=%d type=%s size=%s url=%s",
                    doc.skipnr,
                    doc.doc_type,
                    f"{doc.file_size_mb}MB" if doc.file_size_mb else "?",
                    doc.source_url[:80],
                )
            if total > 20:
                logger.info("  ... and %d more", total - 20)
            return

    processed = 0
    rendered = 0
    skipped = 0
    failed = 0
    failed_ids = set()

    while True:
        with db_context() as db:
            query = (
                db.query(DeiliskipulagDocument)
                .filter(
                    DeiliskipulagDocument.pages_rendered_at.is_(None),
                    DeiliskipulagDocument.doc_type.in_(RENDER_DOC_TYPES),
                )
                .order_by(
                    # Render uppdráttur first (highest value)
                    DeiliskipulagDocument.doc_type.desc(),
                    DeiliskipulagDocument.skipnr,
                )
            )
            if failed_ids:
                query = query.filter(~DeiliskipulagDocument.id.in_(failed_ids))
            batch = query.limit(BATCH_SIZE).all()

            if not batch:
                break

            for doc in batch:
                if args.limit and processed >= args.limit:
                    logger.info(
                        "Limit reached. processed=%d rendered=%d skipped=%d failed=%d",
                        processed,
                        rendered,
                        skipped,
                        failed,
                    )
                    return

                processed += 1

                # Skip files that are too large
                if doc.file_size_mb and doc.file_size_mb > MAX_FILE_SIZE_MB:
                    logger.info(
                        "[%d/%d] SKIP skipnr=%d type=%s (%.1f MB > %d MB limit)",
                        processed,
                        total,
                        doc.skipnr,
                        doc.doc_type,
                        doc.file_size_mb,
                        MAX_FILE_SIZE_MB,
                    )
                    skipped += 1
                    failed_ids.add(doc.id)
                    continue

                max_pages = MAX_PAGES.get(doc.doc_type)
                logger.info(
                    "[%d/%d] skipnr=%d type=%s size=%s max_pages=%s",
                    processed,
                    total,
                    doc.skipnr,
                    doc.doc_type,
                    f"{doc.file_size_mb}MB" if doc.file_size_mb else "?",
                    max_pages or "all",
                )

                page_count_val = multiprocessing.Value("i", 0)
                p = multiprocessing.Process(
                    target=_render_worker,
                    args=(doc.skipnr, doc.doc_type, doc.source_url, max_pages, page_count_val),
                )
                p.start()
                p.join(timeout=args.timeout)

                if p.is_alive():
                    p.terminate()
                    p.join()
                    logger.error("  Timeout for doc id=%d skipnr=%d", doc.id, doc.skipnr)
                    failed_ids.add(doc.id)
                    failed += 1
                elif p.exitcode == 0:
                    doc = db.query(DeiliskipulagDocument).get(doc.id)
                    doc.pages_rendered_at = dt.datetime.utcnow()
                    doc.page_count = page_count_val.value or None
                    db.commit()
                    rendered += 1
                    logger.info("  OK (%d pages)", page_count_val.value)
                else:
                    logger.error(
                        "  Child exited %d for doc id=%d skipnr=%d",
                        p.exitcode,
                        doc.id,
                        doc.skipnr,
                    )
                    failed_ids.add(doc.id)
                    failed += 1

            db.expunge_all()
        logger.info(
            "-- Batch done. processed=%d rendered=%d skipped=%d failed=%d --",
            processed,
            rendered,
            skipped,
            failed,
        )

    logger.info(
        "Done. processed=%d rendered=%d skipped=%d failed=%d",
        processed,
        rendered,
        skipped,
        failed,
    )


if __name__ == "__main__":
    multiprocessing.set_start_method("fork")
    main()
