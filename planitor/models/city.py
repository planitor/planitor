import enum
from collections import namedtuple

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship
from sqlalchemy.types import ARRAY, BIGINT, TEXT, NUMERIC
from sqlalchemy_utils import CompositeArray, CompositeType

from ..utils.kennitala import Kennitala
from ..database import Base

EnumValue = namedtuple("EnumValue", ("slug", "label"))

ColorEnumValue = namedtuple("ColorEnumValue", ("slug", "label", "color"))


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
    approved = ColorEnumValue("samthykkt", "Samþykkt", "green")
    answered_positive = ColorEnumValue("jakvaett", "Jákvætt", "green")
    delayed = ColorEnumValue("frestad", "Frestað", "yellow")

    notice = ColorEnumValue("grenndarkynning", "Samþykkt að grenndarkynna", "yellow")

    directed_to_skipulagsfulltrui = ColorEnumValue(
        "visad-til-skipulagsfulltrua", "Vísað til skipulagsfulltrúa", "yellow"
    )
    directed_to_skipulagsrad = ColorEnumValue(
        "visad-til-skipulags", "Vísað til Skipulags- og samgönguráðs", "yellow"
    )
    directed_to_adalskipulag = ColorEnumValue(
        "visad-til-deildarstjora-adalskipulags",
        "Vísað til umsagnar deildarstjóra aðalskipulags",
        "yellow",
    )
    directed_to_mayor = ColorEnumValue(
        "visad-til-skrifstofu-borgarstjora", "Vísað til skrifstofu borgarstjóra", "yellow"
    )
    directed_to_borgarrad = ColorEnumValue(
        "visad-til-borgarrads", "Vísað til borgarráðs", "yellow"
    )
    directed_to_skipulagssvid = ColorEnumValue(
        "visad-til-skipulagssvids", "Vísað til umhverfis- og skipulagssviðs", "yellow"
    )
    assigned_project_manager = ColorEnumValue(
        "visad-til-verkefnastjora", "Vísað til verkefnisstjóra", "yellow"
    )
    answered_negative = ColorEnumValue("neikvaett", "Neikvætt", "red")
    denied = ColorEnumValue("neitad", "Synjað", "red")
    dismissed = ColorEnumValue("visad-fra", "Vísað frá", "red")
    no_comment = ColorEnumValue("engar-athugasemdir", "Engar athugasemdir", "blue")


class Geoname(Base):
    """ Data that is generated by OSMNames """

    __tablename__ = "geonames"
    osm_id = Column(BIGINT, primary_key=True, index=True, autoincrement=False)
    name = Column(TEXT)
    lon = Column(Numeric)
    lat = Column(Numeric)
    place_rank = Column(Integer)
    city = Column(TEXT)
    importance = Column(NUMERIC)
    alternative_names = Column(TEXT)
    class_ = Column("class", TEXT)
    country = Column(TEXT)
    country_code = Column(TEXT)
    county = Column(TEXT)
    display_name = Column(TEXT)
    housenumbers = Column(TEXT)
    osm_type = Column(TEXT)
    state = Column(TEXT)
    street = Column(TEXT)
    type_ = Column("type", TEXT)
    wikidata = Column(TEXT)
    wikipedia = Column(TEXT)

    east = Column(NUMERIC)
    north = Column(NUMERIC)
    south = Column(NUMERIC)
    west = Column(NUMERIC)

    def __str__(self):
        return self.name


class Housenumber(Base):
    __tablename__ = "housenumbers"
    osm_id = Column(BIGINT, primary_key=True, index=True, autoincrement=False)
    street_name = Column("street", TEXT)
    lon = Column(Numeric)
    lat = Column(Numeric)
    housenumber = Column(TEXT)

    street_id = Column(BIGINT, ForeignKey(Geoname.osm_id))
    street = relationship(Geoname)

    def __str__(self):
        address = self.street_name
        if self.housenumber:
            address = f"{address} {self.housenumber}"
        return address


class Address(Base):
    __tablename__ = "addresses"

    hnitnum = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, server_default=func.now())

    bokst = Column(String, index=True)
    byggd = Column(Integer)
    heiti_nf = Column(String, index=True)
    heiti_tgf = Column(String)
    husnr = Column(Integer, index=True)
    landnr = Column(Integer)
    lat_wgs84 = Column(Numeric)
    long_wgs84 = Column(Numeric)
    lysing = Column(String)
    postnr = Column(Integer)
    serheiti = Column(String)
    stadur_nf = Column(String)
    stadur_tgf = Column(String)
    svaedi_nf = Column(String)
    svaedi_tgf = Column(String)
    svfnr = Column(Integer)
    tegund = Column(String)
    vidsk = Column(String)

    def __str__(self):
        address = self.heiti_nf
        if self.husnr:
            address = f"{address} {self.husnr}{self.bokst}"
        return address

    def get_coordinates(self):
        return self.lat_wgs84, self.long_wgs84


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

    def get_human_kennitala(self):
        return "{}-{}".format(self.kennitala[:6], self.kennitala[6:])


class Municipality(Base):
    __tablename__ = "municipalities"
    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, server_default=func.now())
    name = Column(String)
    slug = Column(String, unique=True, nullable=False)

    geoname_osm_id = Column(BIGINT, ForeignKey(Geoname.osm_id))
    geoname = relationship(Geoname)

    def __str__(self):
        return self.name


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

    def __str__(self):
        return self.name


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    created = Column(DateTime, server_default=func.now())
    start = Column(DateTime, nullable=False, index=True)
    end = Column(DateTime)
    description = Column(String)
    attendant_names = Column(ARRAY(String))
    url = Column(String)

    council_id = Column(Integer, ForeignKey(Council.id))
    council = relationship(Council)

    minutes = relationship("Minute")


class PDFAttachment(Base):
    __tablename__ = "pdf_attachments"

    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, server_default=func.now())
    bucket = Column(String)
    key = Column(String)
    page_count = Column(Integer)
    page_highlight = Column(Integer)
    attachment_id = Column(Integer, ForeignKey("attachments.id"))
    attachment = relationship("Attachment")


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, server_default=func.now())
    url = Column(String)
    type = Column(String, nullable=True)
    label = Column(String)
    length = Column(Integer)
    minute_id = Column(Integer, ForeignKey("minutes.id"))
    minute = relationship("Minute")

    pdf = relationship(PDFAttachment, uselist=False)


class CaseEntity(Base):
    __tablename__ = "case_entities"
    entity_id = Column(String, ForeignKey("entities.kennitala"), primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"), primary_key=True)
    applicant = Column(Boolean, default=True)
    entity = relationship(Entity)

    # It’s a bit weird that minutes contribute entities to cases. If we update the
    # inquiry field and re-assess the entities mentioned of a minute we cannot remove
    # an entity no longer in the minute because another minute of the same case could
    # have contributed it. This should be ok since inquiries never change.


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    serial = Column(String)
    created = Column(DateTime, server_default=func.now())
    address = Column(String)
    stadgreinir = Column(String)
    headline = Column(String)

    # This field is denormalized, is derived from most recent minute
    status = Column(Enum(CaseStatusEnum), nullable=True)
    updated = Column(DateTime, nullable=True)

    geoname_osm_id = Column(BIGINT, ForeignKey(Geoname.osm_id))
    geoname = relationship(Geoname)

    housenumber_osm_id = Column(BIGINT, ForeignKey(Housenumber.osm_id))
    housenumber = relationship(Housenumber)

    address_id = Column(Integer, ForeignKey(Address.hnitnum), index=True)
    iceaddr = relationship(
        Address
    )  # not `address` because that column is taken for scraped address

    council_id = Column(Integer, ForeignKey(Council.id))
    council = relationship(Council)

    # This case could relate to a deiliskipulag
    plan_id = Column(Integer, ForeignKey(Plan.id))
    plan = relationship(Plan)

    entities = relationship(CaseEntity)

    __table_args__ = (UniqueConstraint("serial", "council_id"),)

    def get_coordinates(self):
        if self.iceaddr:
            return self.iceaddr.get_coordinates()
        if self.housenumber_osm_id:
            return self.housenumber.lat, self.housenumber.lon
        if self.geoname_osm_id:
            return self.geoname.lat, self.geoname.lon


class EntityMention(object):
    """ Used to mark parsed company names inside the inquiry text property. Very
    expensive to calculate on the fly, so we store it here.

    """

    def __init__(self, entity, start, stop):
        self.entity = entity
        self.start = start
        self.stop = stop

    def __composite_values__(self):
        return self.entity, self.start, self.stop

    def __repr__(self):
        return "EntityMention(entity={}, start={}, stop={})".format(
            self.entity.id, self.start, self.stop
        )

    def __eq__(self, other):
        return (
            isinstance(other, EntityMention)
            and other.entity == self.entity
            and other.start == self.start
            and other.stop == self.stop
        )


class Response(Base):
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True)
    order = Column(Integer)
    headline = Column(String)
    contents = Column(String)
    minute = relationship("Minute")
    minute_id = Column(Integer, ForeignKey("minutes.id"), nullable=False, index=True)
    subjects = Column(ARRAY(String))


class Minute(Base):
    __tablename__ = "minutes"

    id = Column(Integer, primary_key=True, index=True)
    serial = Column(String, index=True)
    case_id = Column(Integer, ForeignKey(Case.id), nullable=True, index=True)
    case = relationship(Case)
    status = Column(Enum(CaseStatusEnum), nullable=True)
    meeting_id = Column(Integer, ForeignKey(Meeting.id), nullable=True, index=True)
    meeting = relationship(Meeting)
    headline = Column(String)
    inquiry = Column(String)
    remarks = Column(String)
    lemmas = Column(String)
    subcategory = Column(String)
    participants = Column(ARRAY(String))
    entrants_and_leavers = Column(ARRAY(String))
    responses = relationship(Response, order_by="Response.order")
    stadgreinir = Column(String)

    attachments = relationship(Attachment)

    entity_mentions = Column(
        CompositeArray(
            CompositeType(
                "entity_mention_type",
                [
                    Column("entity_id", String, ForeignKey(Entity.kennitala)),
                    Column("start", Integer),
                    Column("end_", Integer),
                ],
            )
        )
    )

    __table_args__ = (
        Index(
            "ix_lemmas_tsv", func.to_tsvector("simple", lemmas), postgresql_using="gin"
        ),
    )

    def assign_entity_mentions(self, mentions):
        self.entity_mentions = []
        for kennitala, locations in mentions.items():
            for location in locations:
                start, end = location
                self.entity_mentions.append((kennitala, start, end))

    def get_inquiry_mention_tokens(self):
        """ Use `entity_mentions` to mark linkable locations in the `inquiry` text
        """
        s = self.inquiry
        if self.entity_mentions is None:
            entity_mentions = []
        else:
            entity_mentions = list(self.entity_mentions)
        mentions = sorted(entity_mentions, key=lambda i: i[1])

        if not mentions:
            yield (None, s)

        def tokens():

            for i, (kennitala, start, end) in enumerate(mentions):
                if i == 0:
                    # Before first token
                    yield (None, s[0:start])

                # Token
                yield (Kennitala(kennitala), s[start:end])

                if len(mentions) != i + 1:
                    # Up to next token
                    next_start = mentions[i + 1][1]
                    yield (None, s[end:next_start])
                else:
                    # Or to end if this is last iteration
                    yield (None, s[end:])

        for category, text in tokens():
            if not text:
                continue
            yield (category, text)
