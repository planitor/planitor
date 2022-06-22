from markupsafe import Markup

from planitor.search import get_terms_from_query, iter_preview_fragments

LONG_WORD = "s" * 51
LONG_SENTENCE = " ".join(["s" * 5] * 10)


def test_get_terms_from_query():
    assert get_terms_from_query("'cheese' <-> 'monger' | 'foo' & 'bár'") == [
        "cheese",
        "monger",
        "foo",
        "bár",
    ]


def test_iter_preview_fragments():
    assert list(iter_preview_fragments("A B C", {"b"})) == [
        Markup("A <strong>B</strong> C")
    ]


def test_iter_preview_fragments_cancels_cursor_move_at_long_words():
    assert list(iter_preview_fragments(f"{LONG_WORD} B {LONG_WORD}", {"b"})) == [
        Markup("…<strong>B</strong>…")
    ]


def test_iter_preview_fragments_stops_cursor_at_word_breaks():
    assert list(
        iter_preview_fragments(f"{LONG_SENTENCE} B {LONG_SENTENCE}", {"b"})
    ) == [
        Markup(
            "…sssss sssss sssss sssss sssss <strong>B</strong> "
            "sssss sssss sssss sssss sssss…"
        )
    ]


def test_iter_preview_fragments_before():
    assert list(iter_preview_fragments("A B C", {"a"})) == [
        Markup("<strong>A</strong> B C")
    ]


def test_iter_preview_fragments_after():
    assert list(iter_preview_fragments("A B C", {"c"})) == [
        Markup("A B <strong>C</strong>")
    ]


def test_iter_preview_fragments_escapes_document():
    assert list(iter_preview_fragments("<em> B </em>", {"b"})) == [
        Markup("&lt;em&gt; <strong>B</strong> &lt;/em&gt;")
    ]


def test_iter_preview_fragments_joins_consecutive():
    assert list(iter_preview_fragments("A B C", {"b", "c"})) == [
        Markup("A <strong>B C</strong>")
    ]
