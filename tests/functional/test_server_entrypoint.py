import pytest
from fastapi.testclient import TestClient

from bookstore.main import app


@pytest.mark.smoke
def test_the_served_application_starts_with_the_seeded_catalogue():
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        assert client.get("/books").json()["total"] == 6
