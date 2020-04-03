from planitor.postprocess import get_tag_suggestions_for_minute


def test_get_tag_suggestions_for_minute():
    class Minute:
        pass

    m = Minute()
    (m.inquiry, m.remarks, m.headline) = (
        """Að lokinni auglýsingu er lögð fram að nýju umsókn THG Arkitekta ehf. dags.
        27. maí 2019 varðandi breytingu á deiliskipulagi Naustareits vegna lóðarinnar
        nr. 6-10A við Vesturgötu. Í breytingunni felst að heimilt er að koma fyrir
        svölum á austurenda vesturgötu 6-8 og endurbyggja svalir með tröppum á
        Vesturgötu 10. Gististarfsemi heimiluð á 2. hæð Vesturgötu 6-8, samkvæmt uppdr.
        THG Arkitekta ehf. dags. 24. október 2019. Einnig er lögð fram umsögn
        Minjastofnunar Íslands dags. 4. desember 2017. Tillagan var auglýst frá 21.
        nóvember 2019 til og með 6. janúar 2020. Engar athugasemdir bárust. Einnig er
        lögð fram umsögn Íbúaráðs Miðborgar og Hlíða dags. 6. janúar 2020.""",
        """Samþykkt með vísan til heimilda um embættisafgreiðslur skipulagsfulltrúa í
        viðauka við samþykkt um stjórn Reykjavíkurborgar. Vakin er athygli á að
        þinglýsa skal kvöð um gangandi umferð um lóðina Vesturgötu 6-10A að
        Tryggvagötu.""",
        "breyting á deiliskipulagi",
    )
    assert get_tag_suggestions_for_minute(m) == {
        "ær",
        "arkitekt",
        "athugasemd",
        "athygli",
        "auglýsing",
        "austurendi",
        "breyting",
        "deiliskipulag",
        "ehf.",
        "embættis-afgreiðsla",
        "gangandi",
        "gististarfsemi",
        "hæð",
        "heimild",
        "Hlíðar",
        "íbúaráð",
        "Ísland",
        "koma",
        "kvöð",
        "lóð",
        "miðborg",
        "minja-stofnun",
        "nausta-reitur",
        "númer",
        "Reykjavíkurborg",
        "samþykkt",
        "skipulags-fulltrúi",
        "stjórn",
        "svala",
        "svalir",
        "tillaga",
        "trappa",
        "Tryggvagata",
        "umferð",
        "umsögn",
        "umsókn",
        "uppdráttur",
        "var",
        "vestur-gata",
        "Vesturgata",
        "viðauki",
        "vísa",
    }
