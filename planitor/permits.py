from decimal import Decimal, getcontext as decimal_getcontext
from typing import Dict, Optional, Tuple, Iterable, Union
from collections import defaultdict

from sqlakeyset import get_page
from tokenizer import tokenize, TOK

from planitor.models import (
    Minute,
    BuildingTypeEnum,
    PermitTypeEnum,
    Meeting,
    Council,
    Municipality,
)


PermitType = Union[PermitTypeEnum, BuildingTypeEnum]
HintsType = Dict[PermitType, Iterable[Tuple[str, int]]]


permit_type_lemma_hints: HintsType = {
    PermitTypeEnum.nybygging: {
        ("byggja", 1),
    },
    PermitTypeEnum.vidbygging: {
        ("viðbygging", 1),
    },
    PermitTypeEnum.breyting_inni: {
        ("innra", 1),
        ("tæknirými", 1),
        ("baðherbergi", 1),
        ("þreksalur", 1),
        ("innrétta", 1),
    },
    PermitTypeEnum.breyting_uti: {
        ("gluggi", 1),
        ("svalir", 1),
        ("svalalokun", 1),
        ("útihurð", 1),
        ("garður", 1),
        ("djúpgámur", 1),
    },
    PermitTypeEnum.nidurrif: {
        ("rífa", 1),
    },
}


building_type_lemma_hints: HintsType = {
    BuildingTypeEnum.einbylishus: {
        ("einbýlishús", 2),
    },
    BuildingTypeEnum.fjolbylishus: {
        ("fjölbýlishús", 2),
        ("tvíbýlishús", 2),
        ("kjallaraíbúð", 1),
        ("íbúð", 1),
    },
    BuildingTypeEnum.gestahus: {
        ("gestahús", 1),
    },
    BuildingTypeEnum.geymsluskur: {
        ("bílgeymsla", 1),
        ("bílskúr", 1),
    },
    BuildingTypeEnum.hotel: {
        ("hótel", 2),
    },
    BuildingTypeEnum.idnadarhus: {
        ("iðnaðarhús", 1),
    },
    BuildingTypeEnum.parhus: {
        ("parhús", 1),
    },
    BuildingTypeEnum.radhus: {
        ("raðhús", 1),
    },
    BuildingTypeEnum.sumarhus: {
        ("sumarhús", 1),
    },
    BuildingTypeEnum.verslun_skrifstofur: {
        ("verslunarhúsnæði", 1),
        ("skrifstofuhúsnæði", 1),
        ("skrifstofur", 1),
        ("verslun", 1),
        ("snyrtistofa", 1),
        ("skrifstofu- og verslunarhús", 1),
        ("veitingastaður", 1),
        ("pizzustaður", 1),
        ("hjúkunarrými", 1),
        ("líkamsræktarstöð", 1),
        ("æfingarsalur", 1),
        ("rannsóknarstofa", 1),
        ("barsvæði", 1),
        ("lager", 1),
    },
}


def get_highest_scoring_key_from_hints(
    keywords: Iterable[str],
    hints: HintsType,
) -> Optional[PermitType]:
    key_scores = defaultdict(int)
    for key, lemmas in hints.items():
        for lemma, score in lemmas:
            if lemma in keywords:
                key_scores[key] += score
    if len(key_scores):
        top_score, key = sorted(
            ((score, key) for key, score in key_scores.items()), key=lambda i: i[0]
        )[-1]
        return key


class PermitMinute:
    def __init__(self, minute: Minute):
        self.minute = minute
        self.inquiry_tokens = list(tokenize(minute.inquiry)) if minute.inquiry else []
        self.lemmas = self.minute.lemmas.split(", ") if self.minute.lemmas else []
        self.area_added, self.area_subtracted = self.get_area()
        self.permit_type = self.get_permit_type()
        self.building_type = self.get_building_type()
        self.units = None

    def get_area(self) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        decimal_getcontext().prec = 10
        added, subtracted = None, None
        for i, token in enumerate(self.inquiry_tokens):
            if i == len(self.inquiry_tokens) - 1:
                continue
            next = self.inquiry_tokens[i + 1]

            if token.kind != TOK.NUMBER or next.txt != "ferm":
                continue

            value = token.val[0]

            # Do not add up area for B-rými, scan to left
            lookbehind_tokens = [
                tok.txt
                for tok in self.inquiry_tokens[max(0, i - 5) : i + 1]
                if tok.txt not in (None, ".")
            ]
            if "B-rými" in lookbehind_tokens:
                continue

            if lookbehind_tokens[:2] == ["Eftir", "stækkun"]:
                continue

            if "Niðurrif" in lookbehind_tokens:
                subtracted: Decimal = (subtracted or 0) + Decimal(str(value))
            else:
                if added and "Samtals" in lookbehind_tokens:
                    continue
                added: Decimal = (added or 0) + Decimal(str(value))

        return added, subtracted

    def get_permit_type(self):
        return get_highest_scoring_key_from_hints(self.lemmas, permit_type_lemma_hints)

    def get_building_type(self):
        return get_highest_scoring_key_from_hints(self.lemmas, building_type_lemma_hints)


class PermitMinuteView:

    PER_PAGE = 100

    def __init__(self, db, page_bookmark, *filters):
        query = (
            db.query(Minute)
            .join(Meeting)
            .join(Council)
            .join(Municipality)
            .filter(Minute.remarks.op("~")("160 ?/ ?2010"), *filters)
            .order_by(Meeting.start.desc(), Minute.id)
        )

        self.query = query
        self.page = get_page(query, per_page=self.PER_PAGE, page=page_bookmark)

    def __iter__(self):
        for minute in self.page:
            yield PermitMinute(minute)
