from reynir.bintokenizer import tokenize

from planitor.language.search import (
    get_lemmas,
    get_wordbase,
    get_token_lemmas,
    lemmatize_query,
    parse_lemmas,
)


def test_get_wordbase():
    assert get_wordbase("skipulags-fulltrúi") == "fulltrúi"


def test_get_lemmas():
    assert list(
        get_lemmas("Málinu er vísað til umsagnar skipulagsfulltrúa vegna svala.")
    ) == ["mál", "vísa", "umsögn", "fulltrúi", "skipulagsfulltrúi", "svala"]


def test_get_lemmas_includes_numbers():
    assert list(
        get_lemmas(
            "Sótt er um leyfi til að breyta innra skipulagi allra hæða, loka "
            "stigaopi milli 1. og 3. hæðar og opna á milli Austurstrætis 12a og 14."
        )
    ) == [
        "sækja",
        "leyfi",
        "breyta",
        "skipulag",
        "hæð",
        "loka",
        "stigaop",
        "hæð",
        "opna",
        "Austurstræti",
        "12a",
        "14",
    ]


def test_get_token_lemmas_includes_numbers():
    lemmas = []
    for token in tokenize(
        "Sótt er um leyfi til að breyta innra skipulagi allra hæða, loka "
        "stigaopi milli 1. og 3. hæðar og opna á milli Austurstrætis 12a og 14."
    ):
        lemmas.extend(set(get_token_lemmas(token, ignore=None)))
    assert "12a" in lemmas
    assert "12" in lemmas
    assert "14" in lemmas
    assert "Austurstræti" in lemmas


def test_get_lemmas_singularizes_plural_words():
    assert list(get_lemmas("Sömu gömlu þorpararnir.")) == ["þorpari"]


def test_lemmatize_query_for_webquery():
    assert lemmatize_query("veitingastaðir") == "Veitingastaðir or Veitingastaður"
    assert lemmatize_query("skemmdir") == "Skemmd or Skemmdir"


def test_lemmatize_query_capitalize():
    assert lemmatize_query("brautarholti") == "Brautarholt or Brautarholti"


def test_lemmatize_query_unknown_lemma():
    assert lemmatize_query("unknown") == "Unknown"
    assert lemmatize_query("svalir") == "Svalir"


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
        "6",
        "Austurstræti",
    ]


def test_parse_lemmas():
    assert (
        list(
            parse_lemmas(
                "Hopp rafskútuleiga,.\n"
                "US200204.\n"
                "Eyþór Máni Steinarsson og Ægir Þorsteinsson frá Hopp segja frá "
                "reynslunni af starfinu og tölfræði um notkun flotans.\n"
            )
        )
    ) == [
        "hopp",
        "raf-skútu-leiga",
        "US200204",
        "Eyþór Máni Steinarsson",
        "Ægir Þorsteinsson",
        "hopp",
        "segja",
        "reynsla",
        "starf",
        "tölfræði",
        "notkun",
        "floti",
    ]

