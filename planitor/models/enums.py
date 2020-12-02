import enum
from collections import namedtuple


# It would be cleaner to not include the `name` in the namedtuple but on the client
# side pydantic has only serialized the enum value so we don't have the enum identifier
# which is the name. It's only incidental that the slug value is sometimes the same
# as the name, look at `EntityTypeEnum` to see slugs not matching names. This is why
# we added the name attribute to the namedtuple.

EnumSlug = namedtuple("EnumSlug", ("slug", "label"))
EnumValue = namedtuple("EnumValue", ("slug", "label", "name"))
ColorEnumValue = namedtuple("ColorEnumValue", ("slug", "label", "color"))


class CouncilTypeEnum(enum.Enum):
    byggingarfulltrui = EnumValue(
        "byggingarfulltrui", "Byggingarfulltrúi", "byggingarfulltrui"
    )
    skipulagsfulltrui = EnumValue(
        "skipulagsfulltrui", "Skipulagsfulltrúi", "skipulagsfulltrui"
    )
    skipulagsrad = EnumValue("skipulagsrad", "Skipulagsráð", "skipulagsrad")
    borgarrad = EnumValue("borgarrad", "Borgarráð", "borgarrad")
    borgarstjorn = EnumValue("borgarstjorn", "Borgarstjórn", "borgarstjorn")


class PlanTypeEnum(enum.Enum):
    deiliskipulag = EnumValue("deiliskipulag", "Deiliskipulag", "deiliskipulag")
    adalskipulag = EnumValue("adalskipulag", "Aðalskipulag", "adalskipulag")
    svaedisskipulag = EnumValue("svaedisskipulag", "Svæðisskipulag", "svaedisskipulag")


class EntityTypeEnum(enum.Enum):
    person = EnumValue("persona", "Persóna", "person")
    company = EnumValue("fyrirtaeki", "Fyrirtæki", "company")


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
        "visad-til-skrifstofu-borgarstjora",
        "Vísað til skrifstofu borgarstjóra",
        "yellow",
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


class BuildingTypeEnum(enum.Enum):
    einbylishus = EnumSlug("einbylishus", "Einbýlishús")
    fjolbylishus = EnumSlug("fjolbylishus", "Fjölbýlishús")
    gestahus = EnumSlug("gestahus", "Gestahús")
    geymsluskur = EnumSlug("geymsluskur", "Geymsluskúr")
    hotel = EnumSlug("hotel", "Hótel")
    idnadarhus = EnumSlug("idnadarhus", "Iðnaðarhús")
    parhus = EnumSlug("parhus", "Parhús")
    radhus = EnumSlug("radhus", "Raðhús")
    sumarhus = EnumSlug("sumarhus", "Sumarhús")
    verslun_skrifstofur = EnumSlug("verslun_skrifstofur", "Verslun/skrifstofur")


class PermitTypeEnum(enum.Enum):
    nybygging = EnumSlug("nybygging", "Nýbygging")
    vidbygging = EnumSlug("vidbygging", "Viðbygging")
    breyting_inni = EnumSlug("breyting_inni", "Breyting inni")
    breyting_uti = EnumSlug("breyting_uti", "Breyting úti")
    nidurrif = EnumSlug("nidurrif", "Niðurrif")
