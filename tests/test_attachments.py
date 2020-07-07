import pytest

from contextlib import contextmanager
from wand.image import Image

from planitor import attachments


PDF_CONTENTS = b"%PDF-1.7\n\n1 0 obj\n  << >>\nendobj\n\n2 0 obj\n  << /Length 3 0 R >>\nstream\n/DeviceRGB CS\n/DeviceRGB cs\nq\n1.000000 0.000000 -0.000000 1.000000 0.000000 0.000000 cm\n0.768627 0.768627 0.768627 scn\n0.000000 400.000000 m\n400.000000 400.000000 l\n400.000000 0.000000 l\n0.000000 0.000000 l\n0.000000 400.000000 l\nh\nf\nn\nQ\n\nendstream\nendobj\n\n3 0 obj\n  237\nendobj\n\n4 0 obj\n  << /Annots []\n     /Type /Page\n     /MediaBox [ 0.000000 0.000000 400.000000 400.000000 ]\n     /Resources 1 0 R\n     /Contents 2 0 R\n     /Parent 5 0 R\n  >>\nendobj\n\n5 0 obj\n  << /Kids [ 4 0 R ]\n     /Count 1\n     /Type /Pages\n  >>\nendobj\n\n6 0 obj\n  << /Type /Catalog\n     /Pages 5 0 R\n  >>\nendobj\n\nxref\n0 7\n0000000000 65535 f\n0000000010 00000 n\n0000000034 00000 n\n0000000327 00000 n\n0000000349 00000 n\n0000000524 00000 n\n0000000598 00000 n\ntrailer\n<< /ID [ (some) (id) ]\n   /Root 6 0 R\n   /Size 7\n>>\nstartxref\n657\n%%EOF4 0 obj\n<< /Annots [ ] /Type /Page /MediaBox [ 0 0 400 400 ] /Resources 1 0 R /Parent\n5 0 R /Rotate 0 /Contents 2 0 R >>\nendobj\n5 0 obj\n<< /Type /Pages /Kids [ 4 0 R 7 0 R ] /Count 2 >>\nendobj\n6 0 obj\n<< /Info 12 0 R /Pages 5 0 R /Type /Catalog >>\nendobj\n7 0 obj\n<< /BleedBox [ 0 0 400 400 ] /Annots [ ] /Type /Page /ArtBox [ 0 0 400 400\n] /MediaBox [ 0 0 400 400 ] /Resources 8 0 R /Parent 5 0 R /CropBox [ 0 0\n400 400 ] /Rotate 0 /Contents 9 0 R /TrimBox [ 0 0 400 400 ] >>\nendobj\n8 0 obj\n<< >>\nendobj\n9 0 obj\n<< /Length 237 >> stream\n/DeviceRGB CS\n/DeviceRGB cs\nq\n1.000000 0.000000 -0.000000 1.000000 0.000000 0.000000 cm\n0.768627 0.768627 0.768627 scn\n0.000000 400.000000 m\n400.000000 400.000000 l\n400.000000 0.000000 l\n0.000000 0.000000 l\n0.000000 400.000000 l\nh\nf\nn\nQ\n\nendstream\nendobj\n10 0 obj\n237\nendobj\n11 0 obj\n<< /Producer (macOS Version 10.15.5 \\(Build 19F101\\) Quartz PDFContext, AppendMode 1.1)\n/ModDate (D:20200707140932Z00'00') >>\nendobj\n12 0 obj\n11 0 R\nendobj\nxref\n0 1\n0000000000 65535 f \n4 9\n0000000878 00000 n \n0000001006 00000 n \n0000001071 00000 n \n0000001133 00000 n \n0000001361 00000 n \n0000001382 00000 n \n0000001670 00000 n \n0000001690 00000 n \n0000001832 00000 n \ntrailer\n<< /ID [<736F6D65><2B59A01EC1EE85C77C445131F8AA38E4> ] /Root 6 0 R /Size 13 /Prev 657 >> \nstartxref\n1855\n%%EOF\n"  # noqa


@pytest.fixture
def mock_get_image(monkeypatch):
    @contextmanager
    def get_image(url: str):
        yield Image(blob=PDF_CONTENTS)

    monkeypatch.setattr(attachments, "get_image", get_image)


def test_upload(mock_get_image):
    thumbnails = list(attachments.get_thumbnails("foo"))
    assert len(thumbnails) == 2


def test_update_attachment_with_pdf_thumbnail(
    db, attachment, monkeypatch, mock_get_image
):
    def mock_upload(bytes_io, key):
        pass

    monkeypatch.setattr(attachments, "upload", mock_upload)
    attachments.update_attachment_with_pdf_thumbnails(attachment.id)
