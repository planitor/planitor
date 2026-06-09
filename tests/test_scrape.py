import datetime as dt

import pytest
from scrapy.exceptions import DropItem

from scrape.pipelines import DatabasePipeline
from scrape.spiders.reykjavik_byggingarfulltrui_pdf import (
    get_meeting_name,
    parse_date_from_filename,
)


class DummySpider:
    municipality_slug = "reykjavik"
    council_type_slug = "byggingarfulltrui"


def test_parse_date_from_urlencoded_reykjavik_pdf_filename():
    url = (
        "https://reykjavik.is/sites/default/files/2026-03/"
        "Afgrei%C3%B0slufundur%20byggingarfulltr%C3%BAa%2024.%20mars%202026.pdf"
    )

    assert parse_date_from_filename(url) == dt.datetime(2026, 3, 24)


def test_get_meeting_name_falls_back_to_date():
    assert get_meeting_name("", dt.datetime(2023, 7, 11)) == "2023-07-11"


def test_database_pipeline_drops_meetings_without_start(db):
    pipeline = DatabasePipeline()
    try:
        with pytest.raises(DropItem):
            pipeline.process_item(
                {
                    "url": "https://example.com/missing-date.pdf",
                    "name": "1249",
                    "start": None,
                    "description": "",
                    "minutes": [],
                },
                DummySpider(),
            )

        assert pipeline.db.in_transaction() is False
    finally:
        pipeline.close_spider(DummySpider())
