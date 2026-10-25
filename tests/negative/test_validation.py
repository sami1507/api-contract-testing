import pytest
from fastapi.testclient import TestClient

from bookstore.models import make_isbn13

pytestmark = pytest.mark.negative

VALID_ISBN = make_isbn13("978000000300")


def book(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "title": "Boundary Cases",
        "author": "Test Author",
        "isbn": VALID_ISBN,
        "genre": "fiction",
        "year": 2000,
        "price": 10.0,
    }
    payload.update(overrides)
    return payload


def error_locations(response) -> list[list[str]]:
    return [error["loc"] for error in response.json()["detail"]]


@pytest.mark.parametrize(
    ("overrides", "field"),
    [
        ({"title": ""}, "title"),
        ({"title": "x" * 201}, "title"),
        ({"author": ""}, "author"),
        ({"isbn": "978123"}, "isbn"),
        ({"isbn": "9781234567890"}, "isbn"),
        ({"genre": "cookery"}, "genre"),
        ({"year": 1449}, "year"),
        ({"year": 2101}, "year"),
        ({"price": 0}, "price"),
        ({"price": -3.5}, "price"),
        ({"price": 10_001}, "price"),
    ],
    ids=[
        "empty-title",
        "title-too-long",
        "empty-author",
        "isbn-too-short",
        "isbn-too-long",
        "unknown-genre",
        "year-before-1450",
        "year-after-2100",
        "zero-price",
        "negative-price",
        "price-above-limit",
    ],
)
def test_invalid_book_fields_are_rejected(
    client: TestClient, auth_headers: dict[str, str], overrides: dict, field: str
):
    response = client.post("/books", json=book(**overrides), headers=auth_headers)

    assert response.status_code == 422
    assert ["body", field] in error_locations(response)


def test_isbn_with_a_wrong_check_digit_is_rejected(client: TestClient, auth_headers: dict[str, str]):
    wrong = VALID_ISBN[:-1] + str((int(VALID_ISBN[-1]) + 1) % 10)

    response = client.post("/books", json=book(isbn=wrong), headers=auth_headers)

    assert response.status_code == 422
    assert "invalid ISBN-13 check digit" in response.text


def test_unknown_fields_are_refused_rather_than_silently_dropped(
    client: TestClient, auth_headers: dict[str, str]
):
    response = client.post("/books", json=book(discount=0.5), headers=auth_headers)

    assert response.status_code == 422
    assert ["body", "discount"] in error_locations(response)


def test_a_missing_required_field_is_reported_by_name(client: TestClient, auth_headers: dict[str, str]):
    payload = book()
    del payload["author"]

    response = client.post("/books", json=payload, headers=auth_headers)

    assert response.status_code == 422
    assert ["body", "author"] in error_locations(response)


def test_patch_cannot_change_the_isbn(client: TestClient, auth_headers: dict[str, str]):
    response = client.patch("/books/1", json={"isbn": VALID_ISBN}, headers=auth_headers)

    assert response.status_code == 422
    assert ["body", "isbn"] in error_locations(response)


def test_patch_still_enforces_field_rules(client: TestClient, auth_headers: dict[str, str]):
    response = client.patch("/books/1", json={"year": 3000}, headers=auth_headers)

    assert response.status_code == 422


@pytest.mark.parametrize(
    "query",
    [
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
        {"genre": "cars"},
    ],
    ids=["limit-zero", "limit-above-max", "negative-offset", "unknown-genre-filter"],
)
def test_invalid_query_parameters_are_rejected(client: TestClient, query: dict):
    assert client.get("/books", params=query).status_code == 422
