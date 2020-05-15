import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import register_composites

from scrapy.exceptions import DropItem
from scrapy.utils.project import get_project_settings

from planitor import greynir
from planitor.models import Minute
from planitor.crud import (
    get_or_create_municipality,
    get_or_create_council,
    get_or_create_meeting,
)
from planitor.postprocess import process_minute


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
        muni, created = get_or_create_municipality(self.db, spider.municipality_slug)
        if created:
            self.db.commit()  # Do this so that municipality has an id
        council, created = get_or_create_council(
            self.db, muni, spider.council_type_slug
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
            # If all scraped minute serials are already in database, assume already
            # scraped
            minutes_scraped = {
                m.serial for m in self.db.query(Minute).filter_by(meeting_id=meeting.id)
            }
            if minutes_scraped == {m["serial"] for m in item["minutes"]}:
                raise DropItem("Already processed meeting {}".format(meeting.url))

        self.db.commit()

        # Go through minutes, update case status|entities|tags to reflect meeting minute
        for data in item["minutes"]:
            process_minute(self.db, data, meeting)

        self.db.commit()

        return item
