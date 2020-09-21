from contextlib import contextmanager
from io import BytesIO

import pytest

from planitor import attachments
from planitor.models import PDFAttachment

# PDF with three pages, each page a different color tile for easier debugging
PDF_CONTENTS = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n7 0 obj\n<<\n/Filter /FlateDecode\n/Length 46\n>>\nstream\nx\x9c+\xe4\n\xe4*\xe42P0P01\x80\xe0\xa2T\xaep\xae<.\x03=s3\x13s\x033\x05LFQ:\xba\x864\xa0)\x00-\x18\x0e\xdf\nendstream\nendobj\n4 0 obj\n<<\n/Type /Page\n/MediaBox [0 0 400 400]\n/Rotate 0\n/Resources <<\n>>\n/Contents 7 0 R\n/Parent 2 0 R\n>>\nendobj\n8 0 obj\n<<\n/Filter /FlateDecode\n/Length 57\n>>\nstream\nx\x9c+\xe4\n\xe4*\xe42P0P01\x80\xe0\xa2T\xaep\xae<.\x03=\x03\x03cK#CSs\x05\x03=Kcs#SS\x05C\x85\xa2tt\xb5i@\x03\x00\xe3\xb6\r\xd2\nendstream\nendobj\n5 0 obj\n<<\n/Type /Page\n/MediaBox [0 0 400 400]\n/Rotate 0\n/Resources <<\n>>\n/Contents 8 0 R\n/Parent 2 0 R\n>>\nendobj\n9 0 obj\n<<\n/Filter /FlateDecode\n/Length 39\n>>\nstream\nx\x9c+\xe4\n\xe4*\xe42P0P01\x80\xe0\xa2T\xaep\xae<.C\x05\x90`Q:\xba\\\x1aP\x03\x00\x1e\x92\n\x9c\nendstream\nendobj\n6 0 obj\n<<\n/Type /Page\n/MediaBox [0 0 400 400]\n/Rotate 0\n/Resources <<\n>>\n/Contents 9 0 R\n/Parent 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [4 0 R 5 0 R 6 0 R]\n/Count 3\n>>\nendobj\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n3 0 obj\n<<\n/CreationDate (D:20200708145226Z00'00')\n/Producer (www.ilovepdf.com)\n/ModDate (D:20200709143721Z)\n>>\nendobj\nxref\n0 10\n0000000000 65535 f\r\n0000000781 00000 n\r\n0000000712 00000 n\r\n0000000830 00000 n\r\n0000000132 00000 n\r\n0000000374 00000 n\r\n0000000598 00000 n\r\n0000000015 00000 n\r\n0000000246 00000 n\r\n0000000488 00000 n\r\ntrailer\n<<\n/Size 10\n/Root 1 0 R\n/Info 3 0 R\n/ID [<77538142F2CC686FD3DD4C110F23C673> <4572CDD3AFDB9A2FF78FD9792939ABE4>]\n>>\nstartxref\n949\n%%EOF\n"  # noqa


@pytest.fixture
def mock_get_url_bytestring(monkeypatch):
    @contextmanager
    def get_url_bytestring(url: str):
        yield PDF_CONTENTS

    monkeypatch.setattr(attachments, "get_url_bytestring", get_url_bytestring)


def test_get_pdf_page_count():
    assert attachments.get_pdf_page_count(PDF_CONTENTS) == 3


def test_update_pdf_attachment(db, attachment, mock_get_url_bytestring, mocker):
    attachment.type = "application/pdf"
    upload = mocker.patch("planitor.attachments.upload")
    attachments._update_pdf_attachment(attachment, db)
    assert upload.assert_called_once
    byte_string, key = upload.call_args[0]
    assert isinstance(byte_string, BytesIO)
    assert byte_string.closed
    assert key == "development/attachments/1.pdf"
    assert db.query(PDFAttachment).count() == 1
