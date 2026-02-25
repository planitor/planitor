"""Re-render unrendered PDF attachments and migrate PDFs to MinIO.

Downloads each PDF from its original URL, uploads the full PDF to MinIO,
renders page images as JPEG, and uploads those to MinIO.
Also cleans up duplicate pdf_attachments records before processing.

Each PDF is rendered in a child process to isolate pypdfium2 memory leaks.

Usage:
    docker compose exec -T planitor python scripts/render_unrendered_pdfs.py
    docker compose exec -T planitor python scripts/render_unrendered_pdfs.py --limit 5
    docker compose exec -T planitor python scripts/render_unrendered_pdfs.py --dry-run
"""

import argparse
import datetime as dt
import logging
import multiprocessing
import sys
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

BATCH_SIZE = 50


def _cleanup_duplicates(db):
    """Delete duplicate pdf_attachments, keeping the one with pages_rendered_at set
    (or the highest id if both NULL)."""
    from sqlalchemy import func, text

    from planitor.models import PDFAttachment

    # Find attachment_ids with more than one pdf_attachment record
    dupes = (
        db.query(PDFAttachment.attachment_id)
        .group_by(PDFAttachment.attachment_id)
        .having(func.count(PDFAttachment.id) > 1)
        .all()
    )
    if not dupes:
        logger.info("No duplicate pdf_attachments found")
        return 0

    deleted = 0
    for (attachment_id,) in dupes:
        records = (
            db.query(PDFAttachment)
            .filter(PDFAttachment.attachment_id == attachment_id)
            .order_by(
                # Prefer records with pages_rendered_at set, then highest id
                PDFAttachment.pages_rendered_at.desc().nullslast(),
                PDFAttachment.id.desc(),
            )
            .all()
        )
        # Keep the first (best) record, delete the rest
        for record in records[1:]:
            db.delete(record)
            deleted += 1

    db.commit()
    logger.info("Deleted %d duplicate pdf_attachment records", deleted)
    return deleted


def _download_pdf(url: str, s3_bucket: str, s3_key: str) -> bytes:
    """Try downloading PDF from source URL, fall back to S3 if 404."""
    from urllib.error import HTTPError

    try:
        with urlopen(url) as resource:
            return resource.read()
    except HTTPError as e:
        if e.code == 404 and s3_bucket and s3_key:
            import boto3

            from planitor import config

            s3 = boto3.client(
                "s3",
                region_name=config.get("AWS_DEFAULT_REGION"),
                aws_access_key_id=config.get("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=config.get("AWS_SECRET_ACCESS_KEY"),
            )
            buf = BytesIO()
            s3.download_fileobj(s3_bucket, s3_key, buf)
            pdf_bytes = buf.getvalue()
            buf.close()
            logging.getLogger(__name__).info("  Fetched from S3: %s/%s", s3_bucket, s3_key)
            return pdf_bytes
        raise


def _render_worker(attachment_id: int, url: str, key: str, s3_bucket: str, s3_key: str):
    """Run in child process. Downloads PDF, uploads to MinIO, renders pages."""
    from planitor.attachments import render_pdf_pages, upload

    pdf_bytes = _download_pdf(url, s3_bucket, s3_key)

    # Upload full PDF to MinIO
    buf = BytesIO(pdf_bytes)
    upload(buf, key)
    buf.close()

    # Render page images
    render_pdf_pages(pdf_bytes, attachment_id)


def main():
    parser = argparse.ArgumentParser(
        description="Re-render unrendered PDFs and migrate to MinIO"
    )
    parser.add_argument(
        "--limit", type=int, default=0, help="Limit number of PDFs to process"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=50,
        help="Skip PDFs with more than N pages (default 50)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be processed without doing it",
    )
    args = parser.parse_args()

    from planitor import ENV
    from planitor.database import db_context
    from planitor.models import Attachment, PDFAttachment

    with db_context() as db:
        # Step 1: Clean up duplicates
        _cleanup_duplicates(db)

        # Step 2: Count unrendered
        total = (
            db.query(PDFAttachment)
            .filter(PDFAttachment.pages_rendered_at.is_(None))
            .count()
        )
        logger.info("Unrendered PDF attachments: %d", total)

        if args.dry_run:
            unrendered = (
                db.query(PDFAttachment)
                .join(Attachment)
                .filter(PDFAttachment.pages_rendered_at.is_(None))
                .order_by(PDFAttachment.id)
                .all()
            )
            for pdf_att in unrendered:
                logger.info(
                    "  [dry-run] attachment_id=%d pages=%s url=%s",
                    pdf_att.attachment_id,
                    pdf_att.page_count,
                    pdf_att.attachment.url if pdf_att.attachment else "N/A",
                )
            return

    # Step 3: Process in batches
    processed = 0
    failed = 0
    failed_ids = set()  # Track failed IDs to avoid infinite retry loops

    while True:
        with db_context() as db:
            query = (
                db.query(PDFAttachment)
                .join(Attachment)
                .filter(
                    PDFAttachment.pages_rendered_at.is_(None),
                    PDFAttachment.page_count > 0,
                    PDFAttachment.page_count <= args.max_pages,
                )
                .order_by(PDFAttachment.id)
            )
            if failed_ids:
                query = query.filter(~PDFAttachment.attachment_id.in_(failed_ids))
            batch = query.limit(BATCH_SIZE).all()

            if not batch:
                break

            for pdf_att in batch:
                processed += 1
                if args.limit and processed > args.limit:
                    logger.info("Limit reached. Processed %d, failed %d.", processed - 1, failed)
                    return

                attachment = pdf_att.attachment
                if not attachment or not attachment.url:
                    logger.warning(
                        "[%d] Skipping attachment_id=%d — no URL",
                        processed,
                        pdf_att.attachment_id,
                    )
                    failed_ids.add(pdf_att.attachment_id)
                    failed += 1
                    continue

                key = f"{ENV}/attachments/{attachment.id}.pdf"
                logger.info(
                    "[%d/%d] attachment_id=%d (%s pages) %s",
                    processed,
                    total,
                    pdf_att.attachment_id,
                    pdf_att.page_count or "?",
                    attachment.url[:80],
                )

                # Fork a child process so pypdfium2/PIL memory is reclaimed
                p = multiprocessing.Process(
                    target=_render_worker,
                    args=(pdf_att.attachment_id, attachment.url, key, pdf_att.bucket, pdf_att.key),
                )
                p.start()
                p.join(timeout=120)  # 2 minute timeout per PDF

                if p.is_alive():
                    p.terminate()
                    p.join()
                    logger.error(
                        "  Timeout for attachment_id=%d", pdf_att.attachment_id
                    )
                    failed_ids.add(pdf_att.attachment_id)
                    failed += 1
                elif p.exitcode == 0:
                    pdf_att.bucket = "planitor-pdfs"
                    pdf_att.key = key
                    pdf_att.pages_rendered_at = dt.datetime.utcnow()
                    db.commit()
                    logger.info("  OK")
                else:
                    logger.error(
                        "  Child exited %d for attachment_id=%d",
                        p.exitcode,
                        pdf_att.attachment_id,
                    )
                    failed_ids.add(pdf_att.attachment_id)
                    failed += 1

            db.expunge_all()
        logger.info("-- Batch done, %d processed, %d failed --", processed, failed)

    logger.info("Done. Processed %d, failed %d.", processed, failed)


if __name__ == "__main__":
    multiprocessing.set_start_method("fork")
    main()
