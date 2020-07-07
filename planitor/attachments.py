from contextlib import contextmanager
from io import BytesIO
from typing import Iterator, Tuple
from urllib.request import urlopen

import boto3
import dramatiq

from wand.image import Image
from wand.color import Color

from . import config
from .database import db_context
from .models import Attachment, AttachmentThumbnail

s3 = boto3.client(
    "s3",
    region_name=config.get("AWS_DEFAULT_REGION"),
    aws_access_key_id=config.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=config.get("AWS_SECRET_ACCESS_KEY"),
)
BUCKET_NAME = "planitor"


def upload(bytes_io_file: BytesIO, key: str) -> None:
    s3.upload_fileobj(
        bytes_io_file, BUCKET_NAME, key, ExtraArgs={"ContentType": "image/png"}
    )


@contextmanager
def get_image(url: str):
    with urlopen(url) as resource:
        with Image(file=resource, resolution=288) as image:
            yield image


def get_thumbnails(url: str) -> Iterator[Tuple[int, Image]]:
    with get_image(url) as image:
        for page, thumbnail in enumerate(image.sequence):
            with Image(thumbnail, resolution=288) as thumbnail:
                thumbnail.background_color = Color("#fff")
                thumbnail.alpha_channel = "remove"
                width = min(thumbnail.width, 4_096)
                thumbnail.transform(resize=f"{width}x")
                yield page, thumbnail


@dramatiq.actor
def update_attachment_with_pdf_thumbnails(id: int) -> None:
    with db_context() as db:
        attachment = db.query(Attachment).get(id)
        if attachment is None:
            return
        if attachment.type != "application/pdf":
            return
        for page, thumbnail in get_thumbnails(attachment.url):
            key = f"attachments/{attachment.id}/{page}.png"
            upload(BytesIO(thumbnail.make_blob("PNG")), key)
            db.add(
                AttachmentThumbnail(attachment=attachment, bucket=BUCKET_NAME, key=key)
            )
        db.commit()


"""
m = db.query(Meeting).filter_by(name="77").first()
for min in db.query(Minute).filter(Minute.meeting == m):
    for a in db.query(Attachment).filter(Attachment.minute == min):
        if a.url and a.type == "application/pdf":
            break

from planitor.attachments import update_attachment_with_pdf_thumbnails
update_attachment_with_pdf_thumbnails(a.id)
"""
