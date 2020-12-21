import enum
from collections import namedtuple

"""
A special Enum that plays well with ``pydantic`` and ``mypy``, while allowing
human-readable labels similarly to ``django.db.models.enums.Choices``.
"""


class ChoicesMeta(enum.EnumMeta):
    """A metaclass for creating a enum choices."""

    def __new__(metacls, classname, bases, classdict):
        labels = []
        for key in classdict._member_names:
            value = classdict[key]
            if (
                isinstance(value, (list, tuple))
                and len(value) > 1
                and isinstance(value[-1], (str,))  # Here we could add translation strings
            ):
                *value, label = value
                if len(value) > 1:
                    value = tuple(value)
                else:
                    value = value[0]
            else:
                label = key.replace("_", " ").title()
            labels.append(label)
            # Use dict.__setitem__() to suppress defenses against double
            # assignment in enum's classdict.
            dict.__setitem__(classdict, key, value)
        cls = super().__new__(metacls, classname, bases, classdict)
        cls._value2label_map_ = dict(zip(cls._value2member_map_, labels))
        # Add a label property to instances of enum which uses the enum member
        # that is passed in as "self" as the value to use when looking up the
        # label in the choices.
        cls.label = property(lambda self: cls._value2label_map_.get(self.value))
        cls.do_not_call_in_templates = True
        return enum.unique(cls)

    def __contains__(cls, member):
        if not isinstance(member, enum.Enum):
            # Allow non-enums to match against member values.
            return any(x.value == member for x in cls)
        return super().__contains__(member)

    @property
    def names(cls):
        empty = ["__empty__"] if hasattr(cls, "__empty__") else []
        return empty + [member.name for member in cls]

    @property
    def choices(cls):
        empty = [(None, cls.__empty__)] if hasattr(cls, "__empty__") else []
        return empty + [(member.value, member.label) for member in cls]

    @property
    def labels(cls):
        return [label for _, label in cls.choices]

    @property
    def values(cls):
        return [value for value, _ in cls.choices]


class Choices(enum.Enum, metaclass=ChoicesMeta):
    """Class for creating enumerated choices."""

    def __str__(self):
        """
        Use value when cast to str, so that Choices set as model instance
        attributes are rendered as expected in templates and similar contexts.
        """
        return str(self.value)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        try:
            new_v = cls(str(v))
        except (TypeError, ValueError):
            raise

        return new_v


# It would be cleaner to not include the `name` in the namedtuple but on the client
# side pydantic has only serialized the enum value so we don't have the enum identifier
# which is the name. It's only incidental that the slug value is sometimes the same
# as the name, look at `EntityTypeEnum` to see slugs not matching names. This is why
# we added the name attribute to the namedtuple.


EnumValue = namedtuple("EnumValue", ("slug", "label", "name"))
ColorEnumValue = namedtuple("ColorEnumValue", ("slug", "label", "color"))


class SubscriptionTypeEnum(Choices):
    case = "malsnumer", "Málsnúmer"
    address = "heimilisfang", "Heimilisfang"
    street = "gata", "Stræti"
    entity = "kennitala", "Kennitala"
    radius = "radius", "Radíus"
    search = "leit", "Leit"


class CouncilTypeEnum(Choices):
    byggingarfulltrui = "byggingarfulltrui", "Byggingarfulltrúi"
    skipulagsfulltrui = "skipulagsfulltrui", "Skipulagsfulltrúi"
    skipulagsrad = "skipulagsrad", "Skipulagsráð"
    borgarrad = "borgarrad", "Borgarráð"
    borgarstjorn = "borgarstjorn", "Borgarstjórn"


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


class BuildingTypeEnum(Choices):
    einbylishus = "einbylishus", "Einbýlishús"
    fjolbylishus = "fjolbylishus", "Fjölbýlishús"
    gestahus = "gestahus", "Gestahús"
    geymsluskur = "geymsluskur", "Geymsluskúr"
    hotel = "hotel", "Hótel"
    idnadarhus = "idnadarhus", "Iðnaðarhús"
    parhus = "parhus", "Parhús"
    radhus = "radhus", "Raðhús"
    sumarhus = "sumarhus", "Sumarhús"
    verslun_skrifstofur = "verslun_skrifstofur", "Verslun/skrifstofur"


class PermitTypeEnum(Choices):
    nybygging = "nybygging", "Nýbygging"
    vidbygging = "vidbygging", "Viðbygging"
    breyting_inni = "breyting_inni", "Breyting inni"
    breyting_uti = "breyting_uti", "Breyting úti"
    nidurrif = "nidurrif", "Niðurrif"
