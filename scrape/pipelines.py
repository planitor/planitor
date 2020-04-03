import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from scrapy.utils.project import get_project_settings

from planitor import greynir
from planitor.language import extract_company_names
from planitor.utils.kennitala import Kennitala
from planitor.crud import (
    get_or_create_municipality,
    get_or_create_council,
    get_or_create_entity,
    get_or_create_case_entity,
    get_or_create_meeting,
    create_minute,
    lookup_icelandic_company_in_entities,
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
        meeting.url = item["url"]
        if not created:
            # We don’t have to process this because these are "append only", in the
            # sense that once they are online they never change
            self.db.add(meeting)
            self.db.commit()
            return

        meeting.description = item["description"]
        meeting.attendant_names = get_names(meeting.description)
        meeting.start = item["start"]

        def apply_entity(case, entity, applicant):
            case_entity, _ = get_or_create_case_entity(self.db, case, entity, applicant)
            if case_entity not in case.entities:
                case.entities.append(case_entity)

        # Go through minutes, update case status|entities|tags to reflect meeting minute
        for data in item["minutes"]:

            entity_items = data.pop("entities", [])

            minute = create_minute(self.db, meeting, **data)
            case = minute.case

            # Create and add applicant companies or persons
            for items in entity_items:  # persons or companies inquiring
                kennitala = Kennitala(items.pop("kennitala"))
                if not kennitala.validate():
                    continue
                entity, _ = get_or_create_entity(self.db, kennitala=kennitala, **items)
                apply_entity(case, entity, applicant=True)

            # Also associate companies mentioned in the inquiry, such as architects
            for co_name in extract_company_names(minute.inquiry):
                for entity in list(
                    lookup_icelandic_company_in_entities(self.db, co_name)
                ):
                    apply_entity(case, entity, applicant=False)

            self.db.add(case)
            self.db.commit()

        return item
