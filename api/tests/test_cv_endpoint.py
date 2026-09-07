"""End-to-end tests for POST /api/v1/cv/parse."""

from fastapi.testclient import TestClient

from app.main import app
from app.routers.cv import MAX_UPLOAD_BYTES

from .conftest import build_pdf

client = TestClient(app)


def _post(content: bytes, filename: str = "cv.pdf"):
    return client.post(
        "/api/v1/cv/parse",
        files={"file": (filename, content, "application/pdf")},
    )


def test_returns_the_extracted_cv(cv_pdf):
    response = _post(cv_pdf)
    assert response.status_code == 200
    body = response.json()
    assert body["page_count"] == 1
    assert body["truncated"] is False
    assert body["character_count"] == len(body["raw_text"])
    assert "MicroHack" in body["raw_text"]


def test_rejects_a_non_pdf_with_a_machine_readable_code():
    response = _post(b"just some text", filename="cv.txt")
    assert response.status_code == 415
    assert response.json()["code"] == "INVALID_PDF"


def test_rejects_an_empty_upload():
    response = _post(b"")
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_PDF"


def test_rejects_a_file_over_the_cap():
    oversized = b"%PDF-" + b"\x00" * (MAX_UPLOAD_BYTES + 1)
    response = _post(oversized)
    assert response.status_code == 413
    assert response.json()["code"] == "FILE_TOO_LARGE"


def test_a_scan_gets_an_actionable_message(scanned_pdf):
    response = _post(scanned_pdf)
    assert response.status_code == 422
    assert response.json()["code"] == "PARSE_FAILED"


def test_the_endpoint_is_documented():
    schema = client.get("/openapi.json").json()
    assert "/api/v1/cv/parse" in schema["paths"]


def test_a_large_but_valid_cv_is_truncated_not_rejected():
    response = _post(build_pdf(["Ligne de CV avec du contenu reel."] * 40, pages=60))
    assert response.status_code == 200
    assert response.json()["truncated"] is True
