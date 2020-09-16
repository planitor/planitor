import os

from scrapy.exceptions import DropItem
from scrapy.utils.project import get_project_settings
from sentry_sdk import capture_exception
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import register_composites

from planitor import greynir
from planitor.crud import (
    get_or_create_council,
    get_or_create_meeting,
    get_or_create_municipality,
)
from planitor.models import Minute
from planitor.postprocess import process_minutes


def get_connection_string():
    database_url = get_project_settings().get("DATABASE_URL")
    if database_url is not None:
        return database_url
    return os.environ.get("DATABASE_URL", "postgresql://planitor:@localhost/planitor")


def get_names(text):
    names = set()
    if "Þessi sátu fundinn: " in text:
        _, text = text.split("Þessi sátu fundinn: ", 1)
    for sentence in greynir.parse(text)["sentences"]:
        if sentence.tree:
            names.update(sentence.tree.persons)
    return names


class DatabasePipeline(object):
    def __init__(self):
        connection_string = get_connection_string()
        engine = create_engine(connection_string, connect_args={})
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.db = SessionLocal()
        register_composites(self.db.connection())

    def close_spider(self, spider):
        self.db.close()

    def process_item(self, item, spider):
        if item is None:
            raise DropItem

        muni, created = get_or_create_municipality(self.db, spider.municipality_slug)
        if created:
            self.db.commit()  # Do this so that municipality has an id
        council, created = get_or_create_council(
            self.db,
            muni,
            spider.council_type_slug,
            label=getattr(spider, "council_label", None),
        )
        if created:
            self.db.commit()

        meeting, created = get_or_create_meeting(self.db, council, item["name"])

        if created:
            meeting.url = item["url"]
            meeting.description = item["description"]
            meeting.attendant_names = get_names(meeting.description)
            meeting.start = item["start"]
        else:
            # If meeting already has at least one minute, assume meeting already scraped
            if self.db.query(Minute).filter(Minute.meeting == meeting).count():
                return None

        self.db.commit()

        process_minutes(self.db, item["minutes"], meeting)

        return item
