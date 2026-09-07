"""Unit tests for the deterministic extraction layer."""

import pytest

from app.errors import INVALID_PDF, PARSE_FAILED, ProtuneError
from app.services.cv_parser import MAX_CHARACTERS, extract_text

from .conftest import SAMPLE_CV, build_pdf


def test_reads_the_text_of_a_real_cv(cv_pdf):
    result = extract_text(cv_pdf)
    assert result.page_count == 1
    assert not result.truncated
    assert "Datathon Alpha AI" in result.raw_text
    assert "TOEIC 810" in result.raw_text


def test_counts_every_page(cv_pdf):
    assert extract_text(build_pdf(SAMPLE_CV, pages=3)).page_count == 3


def test_normalises_ragged_whitespace(cv_pdf):
    text = extract_text(cv_pdf).raw_text
    assert "  " not in text
    assert "\n\n\n" not in text
    assert text == text.strip()


def test_rejects_a_file_that_is_not_a_pdf():
    with pytest.raises(ProtuneError) as caught:
        extract_text(b"PK\x03\x04 this is a .docx")
    assert caught.value.code == INVALID_PDF
    assert caught.value.status_code == 415


def test_rejects_a_corrupted_pdf():
    with pytest.raises(ProtuneError) as caught:
        extract_text(b"%PDF-1.7\nbut the rest is garbage")
    assert caught.value.code == INVALID_PDF


def test_explains_that_a_scan_cannot_be_analysed(scanned_pdf):
    with pytest.raises(ProtuneError) as caught:
        extract_text(scanned_pdf)
    assert caught.value.code == PARSE_FAILED
    assert caught.value.status_code == 422
    assert "scan" in caught.value.message.lower()


def test_truncates_an_oversized_cv():
    result = extract_text(build_pdf(SAMPLE_CV, pages=200))
    assert result.truncated
    assert len(result.raw_text) == MAX_CHARACTERS
