import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from scrapy.exceptions import DropItem
from scrapy.utils.project import get_project_settings

from planitor import greynir
from planitor.models import Base, CaseStatusEnum
from planitor.crud import (
    get_or_create_municipality,
    get_or_create_council,
    get_or_create_entity,
    get_or_create_meeting,
    get_or_create_tag,
    get_or_create_case_tag,
    create_minute,
)


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


def get_case_status_from_minute(minute):
    if minute.remarks.startswith("Samþykkt."):
        return CaseStatusEnum.approved
    if minute.remarks.startswith("Frestað."):
        return CaseStatusEnum.delayed
    if minute.remarks.startswith("Jákvætt."):
        return CaseStatusEnum.answered_positive
    if minute.remarks.startswith("Neikvætt. "):
        return CaseStatusEnum.answered_negative
    return None


def get_tag_suggestions_for_minute(minute):
    text = "\n".join((minute.inquiry, minute.remarks, minute.headline))
    tags = set()
    for sentence in greynir.parse(text)["sentences"]:
        if sentence.tree is None:
            continue
        matches = sentence.tree.all_matches("(NP-POSS | NP-SUBJ)")
        tags.update([m.canonical_np for m in matches if m.canonical_np])
    return tags


class DatabasePipeline(object):
    def __init__(self):
        connection_string = get_connection_string()
        engine = create_engine(connection_string, connect_args={})
        Base.metadata.create_all(bind=engine)  # TODO remove
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.db = SessionLocal()

    def close_spider(self, spider):
        self.db.commit()
        self.db.close()

    def process_item(self, item, spider):
        if spider.name == "reykjavik_byggingarfulltrui":
            muni, created = get_or_create_municipality(
                self.db, spider.municipality_slug
            )
            if created:
                self.db.commit()  # Do this so that municipality has an id
            council, created = get_or_create_council(
                self.db, muni, spider.council_type_slug
            )
            if created:
                self.db.commit()
        else:
            # Unsuppored spider, no need to process
            raise DropItem(item)

        meeting, created = get_or_create_meeting(self.db, council, item["name"])
        if not created:
            # We don’t have to process this because these are "append only", in the
            # sense that once they are online they never change
            raise DropItem(item)

        meeting.description = item["description"]
        meeting.attendant_names = get_names(meeting.description)
        meeting.start = item["start"]

        # Go through minutes, update case status|entities|tags to reflect meeting minute
        for data in item["minutes"][:20]:  # TODO remove limit of 2

            entities = data.pop("entities", [])

            minute = create_minute(self.db, meeting, **data)
            case = minute.case
            case.status = get_case_status_from_minute(minute)

            for items in entities:  # persons or companies inquiring
                entity, _ = get_or_create_entity(self.db, **items)
                if entity not in case.entities:
                    case.entities.append(entity)

            for tag in get_tag_suggestions_for_minute(minute):
                tag, _ = get_or_create_tag(self.db, tag)
                case_tag, _ = get_or_create_case_tag(self.db, tag, case)
                case_tag.minute = minute
                if case_tag not in case.tags:
                    case.tags.append(case_tag)

            self.db.add(case)
            self.db.commit()

        return item
