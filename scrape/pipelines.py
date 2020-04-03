import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from scrapy.utils.project import get_project_settings

from planitor import greynir
from planitor.utils.kennitala import Kennitala
from planitor.crud import (
    get_or_create_municipality,
    get_or_create_council,
    get_or_create_entity,
    get_or_create_meeting,
    create_minute,
)


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

    def close_spider(self, spider):
        self.db.commit()
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
        if not created:
            # We don’t have to process this because these are "append only", in the
            # sense that once they are online they never change
            return

        meeting.description = item["description"]
        meeting.attendant_names = get_names(meeting.description)
        meeting.start = item["start"]

        # Go through minutes, update case status|entities|tags to reflect meeting minute
        for data in item["minutes"]:

            entities = data.pop("entities", [])

            minute = create_minute(self.db, meeting, **data)
            case = minute.case

            for items in entities:  # persons or companies inquiring
                kennitala = Kennitala(items.pop("kennitala"))
                if not kennitala.validate():
                    continue
                entity, _ = get_or_create_entity(self.db, kennitala=kennitala, **items)
                if entity not in case.entities:
                    case.entities.append(entity)

            self.db.add(case)
            self.db.commit()

        return item
