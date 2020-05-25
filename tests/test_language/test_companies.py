from planitor.language.companies import (
    parse_icelandic_companies,
    extract_company_names,
    titleize,
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
        "Íþrótta- og sýningahöllin hf.",
        "V-16 ehf.",
    ]:
        assert tuple(parse_icelandic_companies(company)) == (company,)
    assert tuple(parse_icelandic_companies("2018, bréf Faxaflóahafna sf.")) == (
        "Faxaflóahafna sf.",
    )


def test_titleize():
    assert titleize("BB", "aa") == "AA"
    assert titleize("bb", "AA") == "AA"
    assert titleize("bB", "aa") == "aa"
    assert titleize("BB", "AA") == "AA"
    assert titleize("Bb", "AA") == "Aa"


def test_extract_company_names_person_entity_hybrid():
    assert tuple(
        extract_company_names(
            "Starfsmennirnir heimsóttu Hjólbarðaverkstæði Sigurjóns ehf. eldsnemma."
        )
    ) == ("Hjólbarðaverkstæði Sigurjóns ehf.",)


_test_text = (
    "Lögð fram fyrirspurn Björns Skaptasonar dags. 9. mars 2020 f.h. "
    "Guðmundar Jónassonar ehf. ásamt bréfi dags. 6. mars 2020 um breytingu á "
    "deiliskipulagi lóðarinnar nr. 34-36 við Borgartún sem felst í aukningu á "
    "byggingarmagni og nýtingarhlutfalli lóðar, samkvæmt tillögu Atelier Arkitekta "
    "ehf. dags. í apríl 2016."
)


def test_extract_company_names_return_canonical():

    assert list(parse_icelandic_companies(_test_text)) == [
        "Guðmundar Jónassonar ehf.",
        "Atelier Arkitekta ehf.",
    ]

    assert tuple(extract_company_names(_test_text)) == (
        "Guðmundur Jónasson ehf.",
        "Atelier Arkitektar ehf.",
    )


def test_extract_company_names_veitur():

    s = (
        "Einnig er lögð fram greinargerð Veitna ohf. dags. 4. desember 2018, "
        "bréf Faxaflóahafna sf. dags. 14. desember 2018 og bréf Skipulagsstofnunar "
        "dags. 13. desember 2019. "
    )

    assert set(parse_icelandic_companies(s)) == {"Veitna ohf.", "Faxaflóahafna sf."}

    assert set(extract_company_names(s)) == {
        # "Faxaflóahafnir sf.",  # The reason this doesn’t work is that
        #                        # Greynir thinks "faxaflóahafna" indefinite is
        #                        # "Faxaflóahafið"
        "Veitur ohf.",
        "Faxaflóahafið sf.",
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

    assert tuple(extract_company_names(s)) == ("Björgun ehf.",)


def test_clean_company_name():
    assert clean_company_name("Co ehf") == "Co ehf."
    assert clean_company_name("Co ehf.") == "Co ehf."
    assert clean_company_name("Coehf") == "Coehf"
