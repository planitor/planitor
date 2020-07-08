import ctypes
from contextlib import contextmanager
from io import BytesIO
from typing import Iterator, Tuple
from urllib.request import urlopen

import boto3
import dramatiq
from sqlalchemy.orm import Session
from wand.compat import binary
from wand.api import library, libmagick
from wand.color import Color
from wand.image import Image
from wand.sequence import SingleImage

from . import ENV, config
from .database import db_context
from .models import Attachment, AttachmentThumbnail

library.MagickNextImage.argtypes = [ctypes.c_void_p]
library.MagickNextImage.restype = ctypes.c_int

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
def get_pdf_image(url: str):
    with urlopen(url) as resource:
        with Image(file=resource, resolution=300) as pdf_image:
            # pdf_image.depth = 8
            yield pdf_image


@contextmanager
def get_pdf_page_image(pdf_image, index):
    """ We could have used `wand.Image.sequence` but it pushes all pages into memory.
    This is the same code but only yields one page at a time so it's more efficient. """
    wand = pdf_image.wand
    image = library.GetImageFromMagickWand(wand)
    exc = libmagick.AcquireExceptionInfo()
    single_image = libmagick.CloneImages(image, binary(str(index)), exc)
    libmagick.DestroyExceptionInfo(exc)
    single_wand = library.NewMagickWandFromImage(single_image)
    single_image = libmagick.DestroyImage(single_image)
    with SingleImage(single_wand, pdf_image, image) as _:
        with Image(_) as page_image:
            yield page_image
    del single_image
    del single_wand
    del image


def get_thumbnails(url: str) -> Iterator[Tuple[int, Image]]:
    """ Iterate through pages of a pdf, rasterize and resize, yielding `wand.image.Image`
    objects.

    """
    with get_pdf_image(url) as pdf_image:
        library.MagickResetIterator(pdf_image.wand)
        page = 0
        while True:
            if not library.MagickNextImage(pdf_image.wand):
                break
            with get_pdf_page_image(pdf_image, page) as page_image:
                page_image.background_color = Color("#fff")
                page_image.alpha_channel = "remove"
                page_image.transform(resize=f"2000x")
                yield page, page_image
                from wand.display import display

                display(Image(blob=page_image.make_blob("PNG"), format="PNG"))
                page += 1


def _update_attachment_with_pdf_thumbnails(attachment: Attachment, db: Session):
    """ Have a cleaner version of this function for when calling directly, debugging,
    testing etc.
    """
    if attachment.type != "application/pdf":
        return
    for page, thumbnail in get_thumbnails(attachment.url):
        key = f"{ENV}/attachments/{attachment.id}/{page}.png"
        bytes_io = BytesIO(thumbnail.make_blob("PNG"))
        upload(bytes_io, key)
        bytes_io.close()
        db.add(AttachmentThumbnail(attachment=attachment, bucket=BUCKET_NAME, key=key))
    db.commit()


@dramatiq.actor
def update_attachment_with_pdf_thumbnails(id: int) -> None:
    with db_context() as db:
        attachment = db.query(Attachment).get(id)
        if attachment is None:
            return
        _update_attachment_with_pdf_thumbnails(attachment, db)
