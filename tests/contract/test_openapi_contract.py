import jsonschema
import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.contract


def component_schema(client: TestClient, name: str) -> dict:
    """Return a component schema as a standalone document that still resolves its own $refs."""
    components = client.app.openapi()["components"]
    return {"$ref": f"#/components/schemas/{name}", "components": components}


def assert_matches(client: TestClient, instance: object, schema_name: str) -> None:
    schema = component_schema(client, schema_name)
    jsonschema.Draft202012Validator(schema).validate(instance)


def test_openapi_document_describes_every_book_operation(client: TestClient):
    paths = client.app.openapi()["paths"]

    assert set(paths["/books"]) == {"get", "post"}
    assert set(paths["/books/{book_id}"]) == {"get", "patch", "delete"}
    assert set(paths["/health"]) == {"get"}


def test_book_schema_publishes_the_validation_rules(client: TestClient):
    schema = client.app.openapi()["components"]["schemas"]["BookCreate"]["properties"]

    assert schema["year"]["minimum"] == 1450
    assert schema["year"]["maximum"] == 2100
    assert schema["isbn"]["pattern"] == r"^97[89]\d{10}$"
    assert schema["price"]["exclusiveMinimum"] == 0


@pytest.mark.smoke
def test_list_response_matches_the_page_schema(client: TestClient):
    response = client.get("/books")

    assert response.status_code == 200
    assert_matches(client, response.json(), "BookPage")
    for book in response.json()["items"]:
        assert_matches(client, book, "Book")


def test_single_book_response_matches_the_book_schema(client: TestClient):
    response = client.get("/books/1")

    assert response.status_code == 200
    assert_matches(client, response.json(), "Book")


def test_created_book_matches_the_schema_and_echoes_the_input(
    client: TestClient, auth_headers: dict[str, str], new_book_payload: dict
):
    response = client.post("/books", json=new_book_payload, headers=auth_headers)

    assert response.status_code == 201
    assert_matches(client, response.json(), "Book")
    assert {key: response.json()[key] for key in new_book_payload} == new_book_payload


def test_error_responses_follow_the_validation_error_schema(client: TestClient):
    response = client.get("/books", params={"limit": 0})

    assert response.status_code == 422
    assert_matches(client, response.json(), "HTTPValidationError")


def test_not_found_responses_carry_a_detail_message(client: TestClient):
    response = client.get("/books/9999")

    assert response.status_code == 404
    assert response.json() == {"detail": "book 9999 not found"}
