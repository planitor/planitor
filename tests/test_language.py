from planitor.crud import get_or_create_entity
from planitor.language import (
    parse_icelandic_companies,
    lookup_icelandic_company_in_entities,
    find_nominative_icelandic_companies,
    apply_title_casing,
)


def test_parse_icelandic_companies():
    for company in [
        "Miðbæjarhótel/Centerhotels ehf.",
        "Reitir - hótel ehf.",
        "105 Miðborg slhf.",
        "Faxaflóahafnir sf.",
        "Bjarg íbúðafélag hses.",
        "Efstaleitis Apótek ehf.",
    ]:
        assert parse_icelandic_companies(company) == {company}


def test_lookup_in_entities(db):
    name = "Plúsarkitekta ehf"  # Other inflection, missing . at the end
    entity, _ = get_or_create_entity(db, "", name="Plúsarkitektar ehf.", address="")
    db.commit()
    assert lookup_icelandic_company_in_entities(db, name).first() == (entity, 2)


def test_apply_title_case():
    assert apply_title_casing("BB", "aa") == "Aa"
    assert apply_title_casing("bb", "AA") == "AA"
    assert apply_title_casing("bB", "aa") == "aa"
    assert apply_title_casing("BB", "AA") == "Aa"


def test_find_nominative_icelandic_companies():

    assert (
        find_nominative_icelandic_companies(
            """Lögð fram fyrirspurn Björns Skaptasonar dags. 9. mars 2020 f.h.
            Guðmundar Jónassonar ehf. ásamt bréfi dags. 6. mars 2020 um breytingu
            á deiliskipulagi lóðarinnar nr. 34-36 við Borgartún sem felst í aukningu
            á byggingarmagni og nýtingarhlutfalli lóðar, samkvæmt tillögu Atelier
            Arkitekta ehf. dags. í apríl 2016. ."""
        )
        == {"Guðmundur Jónasson ehf.", "Atelier Arkitektar ehf."}
    )

    assert (
        find_nominative_icelandic_companies(
            """Á embættisafgreiðslufundi skipulagsfulltrúa 6. mars 2020 var lögð fram
            fyrirspurn Þóru Ásgeirsdóttur dags. 2. mars 2020 um að hækka húsið á lóð
            nr. 5 við Ægisgötu, yfir íbúð 0503, um eina hæð ásamt því að koma fyrir
            þakgarði, samkvæmt uppdr Zeppelin arkitekta ehf. dags. 14. júní 2004."""
        )
        == {"Zeppelin arkitektar ehf."}
    )

    assert (
        find_nominative_icelandic_companies(
            """Lögð var fram umsókn Kurts og Pí ehf. dags. 6. mars 2020 varðandi breytingu á
            deiliskipulagi."""
        )
        == {"Kurt og Pí ehf."}
    )

    assert (
        find_nominative_icelandic_companies(
            """Í breytingunni felst að færa núverandi grenndarstöð sem er á bílastæði
            samsíða Arnarbakka á núverandi snúningshaus við Leirubakka, samkvæmt
            uppdrætti Hornsteina arkitekta ehf. frá 6. janúar 2020."""
        )
        == {"Hornsteinar arkitektar ehf."}
    )

    assert find_nominative_icelandic_companies(
        "Eftir innlit hjá Plúsarkitektum ehf. var ekki aftur snúið."
    ) == {"Plúsarkitektar ehf."}

    assert (
        find_nominative_icelandic_companies(
            """Samkvæmt uppdrætti verkfræðistofu Ívars Haukssonar ehf. dags. 17.
            mars 2020."""
        )
        == {"Ívar Hauksson ehf."}
    )
