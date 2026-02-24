"""Tests for the search lemmatization module.

Note: These tests use the lemma.solberg.is API which may return different
results than the previous Greynir-based implementation. The API returns
lemmas alphabetically sorted and may return multiple lemmas for ambiguous words.
"""

from planitor.language.search import (
    get_lemmas,
    get_wordbase,
    lemmatize_query,
    filter_stopwords,
)


def test_get_wordbase():
    assert get_wordbase("skipulags-fulltrúi") == "fulltrúi"
    assert get_wordbase("raka-skemmdir") == "skemmdir"
    assert get_wordbase("word") is None


def test_filter_stopwords():
    """Test that stopwords are filtered out."""
    words = ["mál", "til", "vegna", "er", "hús", "við"]
    result = list(filter_stopwords(words))
    assert "til" not in result
    assert "vegna" not in result
    assert "er" not in result
    assert "mál" in result
    assert "hús" in result


def test_get_lemmas_basic():
    """Test basic lemmatization with stopword filtering."""
    lemmas = list(get_lemmas("Málinu er vísað til umsagnar."))
    # Should have basic content words lemmatized
    assert "mál" in lemmas
    assert "vísa" in lemmas
    assert "umsögn" in lemmas
    # Stopwords should be filtered
    assert "til" not in lemmas
    assert "er" not in lemmas


def test_get_lemmas_includes_numbers():
    """Test that numbers and number-letter combinations are preserved."""
    lemmas = list(
        get_lemmas(
            "opna á milli Austurstrætis 12a og 14."
        )
    )
    # Numbers should be included
    assert "12a" in lemmas or "12" in lemmas
    assert "14" in lemmas


def test_lemmatize_query_singularizes():
    """Test that plural forms are lemmatized to singular."""
    result = lemmatize_query("veitingastaðir")
    # Should include the singular lemma
    assert "Veitingastaður" in result


def test_lemmatize_query_handles_unknown():
    """Test that unknown words are preserved."""
    result = lemmatize_query("unknown")
    assert "Unknown" in result


def test_lemmatize_query_quoted_phrase():
    """Test that quoted phrases are preserved and title-cased."""
    result = lemmatize_query('"brautarholt hús"')
    assert result == '"Brautarholt Hús"'


def test_get_lemmas_empty_input():
    """Test that empty input returns empty list."""
    assert list(get_lemmas("")) == []
    assert list(get_lemmas("   ")) == []


def test_get_lemmas_compound_words():
    """Test handling of compound words with dashes."""
    # The API may return compound words with dashes
    # Our with_wordbases function should expand them
    lemmas = list(get_lemmas("skipulagsfulltrúa"))
    assert "skipulagsfulltrúi" in lemmas or any("fulltrúi" in l for l in lemmas)
