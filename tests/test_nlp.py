import pytest
import spacy

def test_spacy_model_available():
    """
    Prüft, ob das deutsche Sprachmodell für Spacy installiert und ladbar ist.
    Wichtig für PDF-Parsing Features.
    """
    try:
        nlp = spacy.load("de_core_news_sm")
        assert nlp is not None
        assert nlp.lang == "de"
    except OSError:
        pytest.fail("Spacy Modell 'de_core_news_sm' nicht gefunden. Bitte mit `python -m spacy download de_core_news_sm` installieren.")
