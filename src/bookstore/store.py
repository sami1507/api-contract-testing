"""In-memory repository. Thread-safe, so it can serve requests from a threaded server."""

from __future__ import annotations

import threading
from collections.abc import Iterable
from typing import Any

from bookstore.models import Book, BookCreate, Genre


class DuplicateISBNError(Exception):
    """Raised when a book with the same ISBN already exists."""


class BookStore:
    def __init__(self, seed: Iterable[BookCreate] = ()) -> None:
        self._lock = threading.Lock()
        self._books: dict[int, Book] = {}
        self._isbns: set[str] = set()
        self._next_id = 1
        for book in seed:
            self.add(book)

    def add(self, data: BookCreate) -> Book:
        with self._lock:
            if data.isbn in self._isbns:
                raise DuplicateISBNError(data.isbn)
            book = Book(id=self._next_id, **data.model_dump())
            self._books[book.id] = book
            self._isbns.add(book.isbn)
            self._next_id += 1
            return book

    def get(self, book_id: int) -> Book | None:
        with self._lock:
            return self._books.get(book_id)

    def find(self, *, genre: Genre | None, limit: int, offset: int) -> tuple[list[Book], int]:
        """Return one page of books in id order, plus the total number that match."""
        with self._lock:
            matching = [book for book in self._books.values() if genre is None or book.genre == genre]
            matching.sort(key=lambda book: book.id)
            return matching[offset : offset + limit], len(matching)

    def update(self, book_id: int, changes: dict[str, Any]) -> Book | None:
        with self._lock:
            current = self._books.get(book_id)
            if current is None:
                return None
            # Re-validate the merged record so constraints still hold after a partial update.
            updated = Book(**{**current.model_dump(), **changes})
            self._books[book_id] = updated
            return updated

    def delete(self, book_id: int) -> bool:
        with self._lock:
            book = self._books.pop(book_id, None)
            if book is None:
                return False
            self._isbns.discard(book.isbn)
            return True
