import os

from reynir import Greynir

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from scrapy.exceptions import DropItem
from scrapy.utils.project import get_project_settings

from planitor.crud import (
    get_or_create_municipality,
    get_or_create_council,
    get_or_create_meeting,
    create_minute,
)


greynir = Greynir()


def get_connection_string():
    database_url = get_project_settings().get("DATABASE_URL")
    if database_url is not None:
        return database_url
    return os.environ.get("DATABASE_URL", "postgresql://planitor:@localhost/planitor")


def get_names(text):
    names = set()
    _, attendants_text = text.split("Þessi sátu fundinn: ", 1)
    for sentence in greynir.parse(attendants_text)["sentences"]:
        names.update(sentence.tree.persons)
    return names


class DatabasePipeline(object):
    def __init__(self):
        connection_string = get_connection_string()
        engine = create_engine(connection_string, connect_args={})
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.db = SessionLocal()

    def close_spider(self, spider):
        self.db.commit()
        self.db.close()

    def process_item(self, item, spider):
        if spider.name == "reykjavik_byggingarfulltrui":
            muni, _ = get_or_create_municipality(self.db, spider.municipality_slug)
            council, _ = get_or_create_council(self.db, muni, spider.council_type_slug)
        else:
            raise DropItem(item)

        meeting, created = get_or_create_meeting(self.db, council, item["name"])
        if not created:
            raise DropItem(item)

        meeting.description = item["description"]
        meeting.attendant_names = get_names(meeting.description)
        meeting.start = item["start"]

        for items in item["minutes"]:
            create_minute(self.db, meeting, **items)

        return item
