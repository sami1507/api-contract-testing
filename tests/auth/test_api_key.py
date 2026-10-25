import pytest
from fastapi.testclient import TestClient

from bookstore.models import make_isbn13

pytestmark = pytest.mark.auth

NEW_BOOK = {
    "title": "Auth Probe",
    "author": "Security Team",
    "isbn": make_isbn13("978000000400"),
    "genre": "science",
    "year": 2022,
    "price": 5.0,
}

WRITE_REQUESTS = [
    ("post", "/books", {"json": NEW_BOOK}),
    ("patch", "/books/1", {"json": {"price": 7.0}}),
    ("delete", "/books/1", {}),
]


@pytest.mark.parametrize(("method", "path", "kwargs"), WRITE_REQUESTS, ids=["create", "update", "delete"])
def test_write_operations_require_an_api_key(client: TestClient, method: str, path: str, kwargs: dict):
    response = getattr(client, method)(path, **kwargs)

    assert response.status_code == 401
    assert response.json()["detail"] == "missing or invalid API key"


@pytest.mark.parametrize(("method", "path", "kwargs"), WRITE_REQUESTS, ids=["create", "update", "delete"])
def test_write_operations_reject_a_wrong_api_key(client: TestClient, method: str, path: str, kwargs: dict):
    response = getattr(client, method)(path, headers={"X-API-Key": "guessed"}, **kwargs)

    assert response.status_code == 401


def test_a_key_sent_as_a_query_parameter_is_not_accepted(client: TestClient):
    response = client.post("/books?x_api_key=test-key-123", json=NEW_BOOK)

    assert response.status_code == 401


def test_read_operations_stay_public(client: TestClient):
    assert client.get("/books").status_code == 200
    assert client.get("/books/1").status_code == 200
    assert client.get("/health").status_code == 200


def test_the_correct_key_allows_writes(client: TestClient, auth_headers: dict[str, str]):
    response = client.post("/books", json=NEW_BOOK, headers=auth_headers)

    assert response.status_code == 201
