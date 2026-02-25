"""Delete expired MinIO page images for old PDF attachments.

Removes page images older than --days (default 90) and nulls out pages_rendered_at
so the template shows a PDF link fallback instead of broken thumbnails.

Usage:
    docker compose exec -T planitor python scripts/cleanup_pdf_pages.py
    docker compose exec -T planitor python scripts/cleanup_pdf_pages.py --days 60
    docker compose exec -T planitor python scripts/cleanup_pdf_pages.py --dry-run
"""

import argparse
import datetime as dt
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from planitor.attachments import MINIO_PAGES_BUCKET, minio
from planitor.database import db_context
from planitor.models import PDFAttachment

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Clean up expired PDF page images from MinIO")
    parser.add_argument("--days", type=int, default=90, help="Delete pages older than N days (default 90)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without deleting")
    args = parser.parse_args()

    cutoff = dt.datetime.utcnow() - dt.timedelta(days=args.days)
    logger.info("Evicting page images rendered before %s (%d days ago)", cutoff.isoformat(), args.days)

    with db_context() as db:
        expired = (
            db.query(PDFAttachment)
            .filter(
                PDFAttachment.pages_rendered_at.isnot(None),
                PDFAttachment.pages_rendered_at < cutoff,
            )
            .all()
        )

        logger.info("Found %d expired PDF attachments", len(expired))
        total_objects = 0

        for pdf_att in expired:
            keys = [
                f"{pdf_att.attachment_id}-page-{i}.jpg"
                for i in range(pdf_att.page_count)
            ]
            total_objects += len(keys)

            if args.dry_run:
                logger.info(
                    "  [dry-run] Would delete %d pages for attachment_id=%d",
                    len(keys),
                    pdf_att.attachment_id,
                )
                continue

            # Delete from MinIO in batches of 1000 (S3 API limit)
            for batch_start in range(0, len(keys), 1000):
                batch = keys[batch_start : batch_start + 1000]
                minio.delete_objects(
                    Bucket=MINIO_PAGES_BUCKET,
                    Delete={"Objects": [{"Key": k} for k in batch], "Quiet": True},
                )

            pdf_att.pages_rendered_at = None

        if not args.dry_run:
            db.commit()

        action = "Would delete" if args.dry_run else "Deleted"
        logger.info(
            "%s %d objects across %d PDF attachments",
            action,
            total_objects,
            len(expired),
        )


if __name__ == "__main__":
    main()
