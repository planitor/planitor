from planitor.language.search import get_lemmas, get_wordbase, parse_lemmas


def test_get_wordbase():
    assert get_wordbase("skipulags-fulltrúi") == "fulltrúi"


def test_get_lemmas(minute):
    assert (
        list(get_lemmas("Málinu er vísað til umsagnar skipulagsfulltrúa vegna svala."))
        == []
    )


def test_get_lemmas_singularizes_plural_words():
    assert list(get_lemmas("Sömu gömlu þorpararnir.")) == ["þorpari"]


def test_parse_lemmas_for_webquery():
    assert list(parse_lemmas("veitingastaðir")) == ["veitingastaður"]
    assert list(parse_lemmas("skemmdir")) == ["skemmd"]


def test_parse_unknown_lemma():
    assert list(parse_lemmas("unknown")) == ["unknown"]
    assert list(parse_lemmas("svalir")) == ["svalir"]


def test_get_lemmas_large_sentence():
    s = (
        "Sótt er um leyfi fyrir tilkynntri framkvæmd þar sem á að fjarlægja núverandi "
        "klæðningu vegna rakaskemmda, grinda og klæða aftur með upprunalegri klæðningu "
        "á húsi nr. 6 við Austurstræti."
    )
    assert list(get_lemmas(s)) == [
        "sækja",
        "leyfi",
        "tilkynna",
        "framkvæmd",
        "fjarlægja",
        "klæðning",
        "skemmd",
        "rakaskemmd",
        "grind",
        "klæði",
        "klæðning",
        "hús",
        "nr.",
        "Austurstræti",
    ]
