"""Backfill MinIO page images for existing PDF attachments.

Downloads each PDF from AWS S3, renders pages as JPEG, and uploads to MinIO.
Each PDF is rendered in a child process to isolate pypdfium2 memory leaks.

Usage:
    docker compose exec -T planitor python scripts/backfill_pdf_pages.py
    docker compose exec -T planitor python scripts/backfill_pdf_pages.py --limit 5
    docker compose exec -T planitor python scripts/backfill_pdf_pages.py --max-pages 50
"""

import argparse
import datetime as dt
import logging
import multiprocessing
import sys
from io import BytesIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

BATCH_SIZE = 50


def _render_worker(attachment_id: int, key: str):
    """Run in child process. Downloads PDF from MinIO, renders pages, uploads to MinIO."""
    from planitor.attachments import MINIO_PDF_BUCKET, render_pdf_pages, minio

    buf = BytesIO()
    minio.download_fileobj(MINIO_PDF_BUCKET, key, buf)
    pdf_bytes = buf.getvalue()
    buf.close()
    render_pdf_pages(pdf_bytes, attachment_id)


def main():
    parser = argparse.ArgumentParser(description="Backfill PDF page images to MinIO")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of PDFs to process")
    parser.add_argument(
        "--max-pages", type=int, default=30,
        help="Skip PDFs with more than N pages (default 30)",
    )
    args = parser.parse_args()

    from planitor.database import db_context
    from planitor.models import PDFAttachment

    processed = 0

    while True:
        with db_context() as db:
            query = db.query(PDFAttachment).filter(
                PDFAttachment.page_count > 0,
                PDFAttachment.page_count <= args.max_pages,
                PDFAttachment.pages_rendered_at.is_(None),
            ).order_by(PDFAttachment.id).limit(BATCH_SIZE)
            batch = query.all()

            if not batch:
                break

            if processed == 0:
                total = db.query(PDFAttachment).filter(
                    PDFAttachment.page_count > 0,
                    PDFAttachment.page_count <= args.max_pages,
                    PDFAttachment.pages_rendered_at.is_(None),
                ).count()
                logger.info(
                    "PDF attachments to process: %d (max %d pages/pdf)",
                    total,
                    args.max_pages,
                )

            for pdf_att in batch:
                processed += 1
                if args.limit and processed > args.limit:
                    logger.info("Done. Processed %d.", processed - 1)
                    return

                logger.info(
                    "[%d] attachment_id=%d (%d pages)",
                    processed,
                    pdf_att.attachment_id,
                    pdf_att.page_count,
                )

                # Fork a child process so all pypdfium2/PIL memory is reclaimed on exit
                p = multiprocessing.Process(
                    target=_render_worker,
                    args=(pdf_att.attachment_id, pdf_att.key),
                )
                p.start()
                p.join()

                if p.exitcode == 0:
                    pdf_att.pages_rendered_at = dt.datetime.utcnow()
                    db.commit()
                    logger.info("  OK")
                else:
                    logger.error(
                        "  Child exited %d for attachment_id=%d",
                        p.exitcode,
                        pdf_att.attachment_id,
                    )

            db.expunge_all()
        logger.info("-- Batch done, %d processed --", processed)

    logger.info("Done. Processed %d.", processed)


if __name__ == "__main__":
    multiprocessing.set_start_method("fork")
    main()
