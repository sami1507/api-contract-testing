import time

import pytest
from fastapi.testclient import TestClient


@pytest.mark.smoke
def test_health_endpoint_reports_ok(client: TestClient):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.smoke
def test_catalogue_is_seeded(client: TestClient):
    response = client.get("/books")

    assert response.status_code == 200
    assert response.json()["total"] == 6


def test_pagination_returns_consecutive_pages(client: TestClient):
    first = client.get("/books", params={"limit": 2}).json()
    second = client.get("/books", params={"limit": 2, "offset": 2}).json()

    assert [book["id"] for book in first["items"]] == [1, 2]
    assert [book["id"] for book in second["items"]] == [3, 4]
    assert first["total"] == second["total"] == 6


def test_last_page_is_shorter_than_the_limit(client: TestClient):
    body = client.get("/books", params={"limit": 4, "offset": 4}).json()

    assert len(body["items"]) == 2
    assert body["offset"] == 4


def test_filter_by_genre_returns_only_matching_books(client: TestClient):
    body = client.get("/books", params={"genre": "technology"}).json()

    assert body["total"] == 2
    assert {book["genre"] for book in body["items"]} == {"technology"}


def test_get_book_by_id(client: TestClient):
    response = client.get("/books/1")

    assert response.status_code == 200
    assert response.json()["title"] == "Designing Quiet Systems"


def test_created_book_is_retrievable_and_has_a_location(
    client: TestClient, auth_headers: dict[str, str], new_book_payload: dict
):
    created = client.post("/books", json=new_book_payload, headers=auth_headers)

    assert created.status_code == 201
    assert created.headers["location"] == f"/books/{created.json()['id']}"
    assert client.get(created.headers["location"]).json()["title"] == new_book_payload["title"]


def test_patch_changes_only_the_supplied_fields(client: TestClient, auth_headers: dict[str, str]):
    before = client.get("/books/1").json()

    response = client.patch("/books/1", json={"price": 39.9}, headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["price"] == 39.9
    assert {k: v for k, v in response.json().items() if k != "price"} == {
        k: v for k, v in before.items() if k != "price"
    }


def test_patch_is_visible_to_later_reads(client: TestClient, auth_headers: dict[str, str]):
    client.patch("/books/3", json={"year": 2015}, headers=auth_headers)

    assert client.get("/books/3").json()["year"] == 2015


def test_delete_removes_the_book(client: TestClient, auth_headers: dict[str, str]):
    response = client.delete("/books/2", headers=auth_headers)

    assert response.status_code == 204
    assert response.content == b""
    assert client.get("/books/2").status_code == 404
    assert client.get("/books").json()["total"] == 5


def test_duplicate_isbn_is_rejected_with_conflict(
    client: TestClient, auth_headers: dict[str, str], new_book_payload: dict
):
    existing = client.get("/books/1").json()
    payload = {**new_book_payload, "isbn": existing["isbn"]}

    response = client.post("/books", json=payload, headers=auth_headers)

    assert response.status_code == 409
    assert response.json()["detail"] == "a book with this ISBN already exists"


def test_deleted_isbn_can_be_reused(client: TestClient, auth_headers: dict[str, str], new_book_payload: dict):
    isbn = client.get("/books/1").json()["isbn"]
    client.delete("/books/1", headers=auth_headers)

    response = client.post("/books", json={**new_book_payload, "isbn": isbn}, headers=auth_headers)

    assert response.status_code == 201


def test_unknown_book_returns_404_for_every_verb(client: TestClient, auth_headers: dict[str, str]):
    assert client.get("/books/999").status_code == 404
    assert client.patch("/books/999", json={"price": 1}, headers=auth_headers).status_code == 404
    assert client.delete("/books/999", headers=auth_headers).status_code == 404


@pytest.mark.performance
def test_list_endpoint_answers_within_the_latency_budget(client: TestClient):
    budget_seconds = 0.5

    started = time.perf_counter()
    response = client.get("/books", params={"limit": 100})
    elapsed = time.perf_counter() - started

    assert response.status_code == 200
    assert elapsed < budget_seconds, f"list took {elapsed:.3f}s, budget is {budget_seconds}s"
