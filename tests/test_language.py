from planitor.crud import get_or_create_entity
from planitor.language import (
    parse_icelandic_companies,
    lookup_icelandic_company_in_entities,
    extract_company_names,
    apply_title_casing,
    clean_company_name,
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


def test_extract_company_names_person_entity_hybrid():
    assert extract_company_names(
        "Starfsmennirnir heimsóttu Hjólbarðaverkstæði Sigurjóns ehf. eldsnemma."
    ) == {"Hjólbarðaverkstæði Sigurjóns ehf."}


def test_extract_company_names_return_canonical():

    assert (
        extract_company_names(
            """Lögð fram fyrirspurn Björns Skaptasonar dags. 9. mars 2020 f.h.
            Guðmundar Jónassonar ehf. ásamt bréfi dags. 6. mars 2020 um breytingu
            á deiliskipulagi lóðarinnar nr. 34-36 við Borgartún sem felst í aukningu
            á byggingarmagni og nýtingarhlutfalli lóðar, samkvæmt tillögu Atelier
            Arkitekta ehf. dags. í apríl 2016. ."""
        )
        == {"Guðmundur Jónasson ehf.", "Atelier Arkitektar ehf."}
    )


def test_extract_company_names_veitur():

    s = (
        "Að lokinni auglýsingu er lögð fram að nýju tillaga umhverfis- og "
        "skipulagssviðs dags í nóvember 2018, uppf. 13. desember 2018, að breytingu "
        "á aðalskipulagi Reykjavíkur 2010-2030 fyrir Sundahöfn vegna landfyllingar "
        "við Klettagarða ásamt umhverfisskýrsla VSÓ ráðgjafar dags. í september "
        "2018, uppf. 14. desember 2018. Einnig er lögð fram greinargerð Veitna ohf. "
        "dags. 4. desember 2018, bréf Faxaflóahafna sf. dags. 14. desember 2018 og "
        "bréf Skipulagsstofnunar dags. 13. desember 2019. "
    )

    assert extract_company_names(s) == {
        # "Faxaflóahafnir sf.",  # The reason this doesn’t work is that
        #                        # Greynir thinks "faxaflóahafna" indefinite is
        #                        # "Faxaflóahafið"
        "Faxaflóahafið sf.",
        "Veitur ohf.",
    }


def test_extract_company_names_fjogur():

    s = (
        "Á embættisafgreiðslufundi skipulagsfulltrúa 18. maí 2018 var lagt fram bréf "
        "Orkustofnunar dags. 7. maí 2018 þar sem óskað er eftir umsögn á umsókn "
        "Björgunar ehf. um leyfi til leitar og rannsókna á möl og sandi af hafsbotni í"
        "Þerneyjarsundi í Kollafirði. Erindinu var vísað til umsagnar skrifstofu "
        "umhverfisgæða og er nú lögð fram að nýju ásamt umsögn skrifstofu "
        "umhverfisgæða dags. 24. maí 2018."
    )

    print(s)
    assert extract_company_names(s) == {
        "Björgun ehf.",
    }


def test_clean_company_name():
    assert clean_company_name("Co ehf") == "Co ehf."
    assert clean_company_name("Co ehf.") == "Co ehf."
    assert clean_company_name("Coehf") == "Coehf"
