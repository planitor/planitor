import datetime as dt
import logging
import re
from contextlib import contextmanager
from io import BytesIO
from typing import Generator
from urllib.request import urlopen

import boto3
import botocore.exceptions
import dramatiq
import pypdfium2
from PIL import Image
from sqlalchemy.orm import Session

from . import ENV, config
from .database import db_context
from .models import Attachment, PDFAttachment

logger = logging.getLogger(__name__)

pdf_page_pattern = re.compile(r"/Type\s*/Page([^s]|$)", re.MULTILINE | re.DOTALL)


minio = boto3.client(
    "s3",
    endpoint_url="http://minio:9000",
    aws_access_key_id=config.get("MINIO_ROOT_USER", default=""),
    aws_secret_access_key=config.get("MINIO_ROOT_PASSWORD", default=""),
    region_name="us-east-1",
)
MINIO_PAGES_BUCKET = "planitor-pages"
MINIO_PDF_BUCKET = "planitor-pdfs"


def _ensure_bucket(bucket: str) -> None:
    try:
        minio.head_bucket(Bucket=bucket)
    except botocore.exceptions.ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code in ("404", "NoSuchBucket"):
            minio.create_bucket(Bucket=bucket)
            logger.info("Created MinIO bucket: %s", bucket)
        else:
            raise


try:
    _ensure_bucket(MINIO_PAGES_BUCKET)
    _ensure_bucket(MINIO_PDF_BUCKET)
except Exception:
    logger.warning("Could not connect to MinIO — bucket check skipped")


def upload(bytes_io_file: BytesIO, key: str) -> None:
    minio.upload_fileobj(
        bytes_io_file, MINIO_PDF_BUCKET, key, ExtraArgs={"ContentType": "application/pdf"}
    )


def get_pdf_page_count(byte_string: bytes) -> int:
    return len(pdf_page_pattern.findall(byte_string.decode("utf-8", "ignore")))


@contextmanager
def get_url_bytestring(url: str):
    with urlopen(url) as resource:
        yield resource.read()


def render_pdf_pages(pdf_bytes: bytes, attachment_id: int) -> int:
    """Render each page of a PDF as JPEG and upload to MinIO.

    Returns the number of pages rendered.
    """
    pdf = pypdfium2.PdfDocument(pdf_bytes)
    page_count = len(pdf)
    for i in range(page_count):
        page = pdf[i]
        # Render at ~1500px width
        scale = 1500 / page.get_width()
        bitmap = page.render(scale=scale)
        pil_image = bitmap.to_pil()
        bitmap.close()
        page.close()
        # Convert to RGB if necessary (RGBA won't save as JPEG)
        if pil_image.mode != "RGB":
            rgb = pil_image.convert("RGB")
            pil_image.close()
            pil_image = rgb
        buf = BytesIO()
        pil_image.save(buf, format="JPEG", quality=85)
        pil_image.close()
        buf.seek(0)
        key = f"{attachment_id}-page-{i}.jpg"
        minio.upload_fileobj(
            buf,
            MINIO_PAGES_BUCKET,
            key,
            ExtraArgs={"ContentType": "image/jpeg"},
        )
        buf.close()
        logger.info("Uploaded %s/%s to MinIO", MINIO_PAGES_BUCKET, key)
    pdf.close()
    return page_count


def _update_pdf_attachment(attachment: Attachment, db: Session) -> None:
    """Download PDF, upload to MinIO, render pages, and upsert PDFAttachment record."""
    if attachment.type != "application/pdf":
        return
    pages_rendered_at = None
    with get_url_bytestring(attachment.url) as resource_bytes:
        page_count = get_pdf_page_count(resource_bytes)
        key = f"{ENV}/attachments/{attachment.id}.pdf"
        bytes_io = BytesIO(resource_bytes)
        upload(bytes_io, key)
        bytes_io.close()
        # Render each page as JPEG and upload to MinIO
        try:
            page_count = render_pdf_pages(resource_bytes, attachment.id)
            pages_rendered_at = dt.datetime.utcnow()
        except Exception:
            logger.exception(
                "Failed to render PDF pages for attachment %s", attachment.id
            )
    # Upsert: update existing record or create new one
    existing = (
        db.query(PDFAttachment)
        .filter(PDFAttachment.attachment_id == attachment.id)
        .first()
    )
    if existing:
        existing.bucket = MINIO_PDF_BUCKET
        existing.key = key
        existing.page_count = page_count
        existing.pages_rendered_at = pages_rendered_at
    else:
        db.add(
            PDFAttachment(
                attachment=attachment,
                bucket=MINIO_PDF_BUCKET,
                key=key,
                page_count=page_count,
                pages_rendered_at=pages_rendered_at,
            )
        )
    db.commit()


@dramatiq.actor
def update_pdf_attachment(id: int) -> None:
    with db_context() as db:
        attachment = db.query(Attachment).get(id)
        if attachment is None:
            return
        _update_pdf_attachment(attachment, db)
