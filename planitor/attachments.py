import re
from contextlib import contextmanager
from io import BytesIO
from typing import Generator
from urllib.request import urlopen

import boto3
import dramatiq
from sqlalchemy.orm import Session

from . import ENV, config
from .database import db_context
from .models import Attachment, PDFAttachment

pdf_page_pattern = re.compile(r"/Type\s*/Page([^s]|$)", re.MULTILINE | re.DOTALL)


s3 = boto3.client(
    "s3",
    region_name=config.get("AWS_DEFAULT_REGION"),
    aws_access_key_id=config.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=config.get("AWS_SECRET_ACCESS_KEY"),
)
BUCKET_NAME = "planitor"


def upload(bytes_io_file: BytesIO, key: str) -> None:
    s3.upload_fileobj(
        bytes_io_file, BUCKET_NAME, key, ExtraArgs={"ContentType": "application/pdf"}
    )  # this method uses threads if necessary


def get_pdf_page_count(byte_string: bytes) -> int:
    return len(pdf_page_pattern.findall(byte_string.decode("utf-8", "ignore")))


@contextmanager
def get_url_bytestring(url: str):
    with urlopen(url) as resource:
        yield resource.read()


def _update_pdf_attachment(attachment: Attachment, db: Session) -> None:
    """Have a cleaner version of this function for when calling directly, debugging,
    testing etc.
    """
    if attachment.type != "application/pdf":
        return
    with get_url_bytestring(attachment.url) as resource_bytes:
        page_count = get_pdf_page_count(resource_bytes)
        key = f"{ENV}/attachments/{attachment.id}.pdf"
        bytes_io = BytesIO(resource_bytes)
        upload(bytes_io, key)
        bytes_io.close()
    db.add(
        PDFAttachment(
            attachment=attachment, bucket=BUCKET_NAME, key=key, page_count=page_count
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
