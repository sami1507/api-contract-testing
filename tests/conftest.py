from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from bookstore import create_app
from bookstore.models import make_isbn13
from bookstore.seed import seed_books
from bookstore.store import BookStore

TEST_API_KEY = "test-key-123"


@pytest.fixture
def client() -> Iterator[TestClient]:
    """A fresh API instance with the demo catalogue, so every test starts from the same data."""
    app = create_app(store=BookStore(seed=seed_books()), api_key=TEST_API_KEY)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"X-API-Key": TEST_API_KEY}


@pytest.fixture
def new_book_payload() -> dict[str, object]:
    return {
        "title": "Testing Without Tears",
        "author": "Sam Reyes",
        "isbn": make_isbn13("978000000100"),
        "genre": "technology",
        "year": 2024,
        "price": 29.5,
    }
