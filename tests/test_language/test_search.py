from planitor.language.search import (
    get_lemmas,
    get_wordbase,
    lemmatize_query,
    get_terms_from_query,
)


def test_get_wordbase():
    assert get_wordbase("skipulags-fulltrúi") == "fulltrúi"


def test_get_lemmas(minute):
    assert (
        list(get_lemmas("Málinu er vísað til umsagnar skipulagsfulltrúa vegna svala."))
        == []
    )


def test_get_lemmas_singularizes_plural_words():
    assert list(get_lemmas("Sömu gömlu þorpararnir.")) == ["þorpari"]


def test_lemmatize_query_for_webquery():
    assert lemmatize_query("veitingastaðir") == "veitingastaður"
    assert lemmatize_query("skemmdir") == "skemmd"


def test_lemmatize_query_capitalize():
    assert lemmatize_query("brautarholti") == "brautarholt"


def test_lemmatize_query_unknown_lemma():
    assert lemmatize_query("unknown") == "unknown"
    assert lemmatize_query("svalir") == "svalir"


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


def test_get_terms_from_query():
    assert get_terms_from_query("'cheese' <-> 'monger' | 'foo' & 'bár'") == [
        "cheese",
        "monger",
        "foo",
        "bár",
    ]
