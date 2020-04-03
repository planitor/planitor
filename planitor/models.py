from collections import namedtuple
import enum

from sqlalchemy import (
    Table,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Date,
    DateTime,
    Numeric,
    Enum,
    func,
    UniqueConstraint,
)
from sqlalchemy.types import ARRAY, BIGINT
from sqlalchemy.orm import relationship

from .database import Base


EnumValue = namedtuple("EnumValue", ("slug", "label"))


class CouncilTypeEnum(enum.Enum):
    byggingarfulltrui = EnumValue("byggingarfulltrui", "Byggingarfulltrúi")
    skipulagsfulltrui = EnumValue("skipulagsfulltrui", "Skipulagsfulltrúi")
    skipulagsrad = EnumValue("skipulagsrad", "Skipulagsráð")
    borgarrad = EnumValue("borgarrad", "Borgarráð")
    borgarstjorn = EnumValue("borgarstjorn", "Borgarstjórn")


class PlanTypeEnum(enum.Enum):
    deiliskipulag = EnumValue("deiliskipulag", "Deiliskipulag")
    adalskipulag = EnumValue("adalskipulag", "Aðalskipulag")
    svaedisskipulag = EnumValue("svaedisskipulag", "Svæðisskipulag")


class EntityTypeEnum(enum.Enum):
    person = EnumValue("persona", "Persóna")
    company = EnumValue("fyrirtaeki", "Fyrirtæki")


class CaseStatusEnum(enum.Enum):
    delayed = EnumValue("frestad", "Frestað")
    approved = EnumValue("samthykkt", "Samþykkt")
    denied = EnumValue("neitad", "Synjað")
    answered_positive = EnumValue("jakvaett", "Jákvætt")
    answered_negative = EnumValue("neikvaett", "Neikvætt")
    no_comment = EnumValue("engar-athugasemdir", "Engar athugasemdir")

    notice = EnumValue("grenndarkynning", "Samþykkt að grenndarkynna")

    directed_to_skipulagsrad = EnumValue(
        "visad-til-skipulags", "Vísað til Skipulags- og samgönguráðs"
    )
    directed_to_adalskipulag = EnumValue(
        "visad-til-deildarstjora-adalskipulags",
        "Vísað til umsagnar deildarstjóra aðalskipulags",
    )
    assigned_project_manager = EnumValue(
        "visad-til-verkefnastjora", "Vísað til verkefnastjóra"
    )


class Geoname(Base):
    __tablename__ = "geonames"
    osm_id = Column(BIGINT, primary_key=True, index=True)
    name = Column(String)
    lon = Column(Numeric)
    lat = Column(Numeric)
    place_rank = Column(Integer)
    city = Column(String)
    importance = Column(Integer)


class Housenumber(Base):
    __tablename__ = "housenumbers"
    osm_id = Column(BIGINT, primary_key=True, index=True)
    street_name = Column("street", String)
    lon = Column(Numeric)
    lat = Column(Numeric)
    housenumber = Column(String)

    street_id = Column(BIGINT, ForeignKey(Geoname.osm_id))
    street = relationship(Geoname)


class Entity(Base):
    # As in "legal entity"; person or company
    __tablename__ = "entities"

    kennitala = Column(String, primary_key=True, index=True)
    created = Column(DateTime, server_default=func.now())
    name = Column(String)
    slug = Column(String)
    website_url = Column(String, nullable=True)
    entity_type = Column(Enum(EntityTypeEnum))
    address = Column(String, nullable=True)
    birthday = Column(Date)

    geoname_osm_id = Column(BIGINT, ForeignKey(Geoname.osm_id), nullable=True)
    geoname = relationship(Geoname)


class Municipality(Base):
    __tablename__ = "municipalities"
    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, server_default=func.now())
    name = Column(String)

    geoname_osm_id = Column(BIGINT, ForeignKey(Geoname.osm_id))
    geoname = relationship(Geoname)


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    created = Column(DateTime, server_default=func.now())

    parent_id = Column(Integer, ForeignKey("plans.id"), nullable=True)
    parent = relationship("Plan", remote_side=[id])

    minicipality_id = Column(Integer, ForeignKey(Municipality.id))
    minicipality = relationship(Municipality)


class Council(Base):
    __tablename__ = "councils"

    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, server_default=func.now())
    name = Column(String)
    active = Column(Boolean, default=True)

    municipality_id = Column(Integer, ForeignKey(Municipality.id), nullable=True)
    municipality = relationship(Municipality)

    council_type = Column(Enum(CouncilTypeEnum))


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    created = Column(DateTime, server_default=func.now())
    start = Column(DateTime)
    end = Column(DateTime, nullable=True)
    description = Column(String, nullable=True)
    attendant_names = Column(ARRAY(String), nullable=True)

    council_id = Column(Integer, ForeignKey(Council.id))
    council = relationship(Council)


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    file_url = Column(String)
    file_type = Column(String, nullable=True)
    name = Column(String)


class Tag(Base):
    __tablename__ = "tags"
    name = Column(String, primary_key=True, index=True)


case_entity_table = Table(
    "case_entities",
    Base.metadata,
    Column("entity_id", String, ForeignKey("entities.kennitala"), primary_key=True),
    Column("case_id", Integer, ForeignKey("cases.id"), primary_key=True),
)


class CaseAttachment(Base):
    # We want to collate all attachments to cases, but they can be associated with a
    # meeting minute about a case where they first appeared
    __tablename__ = "case_attachments"
    attachment_id = Column(Integer, ForeignKey("attachments.id"), primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"), primary_key=True)
    created = Column(DateTime, server_default=func.now())

    minute_id = Column(Integer, ForeignKey("minutes.id"))
    minute = relationship("Minute")


class CaseTag(Base):
    # We want to collate all tags to cases, but they can be associated with a
    # meeting minute about a case where they first appeared
    __tablename__ = "case_tags"
    tag_id = Column(String, ForeignKey("tags.name"), primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"), primary_key=True)
    approved = Column(
        Boolean, default=False
    )  # We want to process suggested tags approved by an admin

    minute_id = Column(Integer, ForeignKey("minutes.id"))
    minute = relationship("Minute")


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    serial = Column(String)
    created = Column(DateTime, server_default=func.now())
    address = Column(String)

    # This field is denormalized, is derived from most recent minute
    status = Column(Enum(CaseStatusEnum), nullable=True)
    updated = Column(DateTime, nullable=True)

    geoname_osm_id = Column(BIGINT, ForeignKey(Geoname.osm_id))
    geoname = relationship(Geoname)

    housenumber_osm_id = Column(BIGINT, ForeignKey(Housenumber.osm_id))
    housenumber = relationship(Housenumber)

    council_id = Column(Integer, ForeignKey(Council.id))
    council = relationship(Council)

    # This case could relate to a deiliskipulag
    plan_id = Column(Integer, ForeignKey(Plan.id))
    plan = relationship(Plan)

    attachments = relationship(CaseAttachment)
    tags = relationship(CaseTag)
    entities = relationship(Entity, secondary=case_entity_table)

    __table_args__ = (UniqueConstraint("serial", "council_id"),)


class Minute(Base):
    __tablename__ = "minutes"

    id = Column(Integer, primary_key=True, index=True)
    serial = Column(String, index=True)
    case_id = Column(Integer, ForeignKey(Case.id), nullable=True)
    case = relationship(Case)
    status = Column(Enum(CaseStatusEnum), nullable=True)
    meeting_id = Column(Integer, ForeignKey(Meeting.id), nullable=True)
    meeting = relationship(Meeting)
    headline = Column(String)
    inquiry = Column(String)
    remarks = Column(String)
