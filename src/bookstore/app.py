"""FastAPI application: a small bookstore API used as the system under test."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response, status

from bookstore.models import Book, BookCreate, BookPage, BookUpdate, Genre
from bookstore.seed import seed_books
from bookstore.store import BookStore, DuplicateISBNError

DEFAULT_API_KEY = "change-me"


def _not_found(book_id: int) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"book {book_id} not found")


def create_app(store: BookStore | None = None, api_key: str = DEFAULT_API_KEY) -> FastAPI:
    repository = store if store is not None else BookStore(seed=seed_books())

    app = FastAPI(
        title="Bookstore API",
        version="1.0.0",
        description="Reference REST API exercised by the contract and functional test suites.",
    )

    def require_api_key(x_api_key: Annotated[str | None, Header()] = None) -> None:
        if x_api_key != api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="missing or invalid API key",
            )

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/books", response_model=BookPage, tags=["books"])
    def list_books(
        genre: Genre | None = None,
        limit: Annotated[int, Query(ge=1, le=100)] = 10,
        offset: Annotated[int, Query(ge=0)] = 0,
    ) -> BookPage:
        items, total = repository.find(genre=genre, limit=limit, offset=offset)
        return BookPage(items=items, total=total, limit=limit, offset=offset)

    @app.get(
        "/books/{book_id}",
        response_model=Book,
        tags=["books"],
        responses={404: {"description": "No book has this id"}},
    )
    def get_book(book_id: int) -> Book:
        book = repository.get(book_id)
        if book is None:
            raise _not_found(book_id)
        return book

    @app.post(
        "/books",
        response_model=Book,
        status_code=status.HTTP_201_CREATED,
        tags=["books"],
        dependencies=[Depends(require_api_key)],
        responses={409: {"description": "A book with this ISBN already exists"}},
    )
    def create_book(payload: BookCreate, response: Response) -> Book:
        try:
            book = repository.add(payload)
        except DuplicateISBNError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="a book with this ISBN already exists",
            ) from None
        response.headers["Location"] = f"/books/{book.id}"
        return book

    @app.patch(
        "/books/{book_id}",
        response_model=Book,
        tags=["books"],
        dependencies=[Depends(require_api_key)],
    )
    def update_book(book_id: int, payload: BookUpdate) -> Book:
        book = repository.update(book_id, payload.model_dump(exclude_unset=True))
        if book is None:
            raise _not_found(book_id)
        return book

    @app.delete(
        "/books/{book_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        tags=["books"],
        dependencies=[Depends(require_api_key)],
    )
    def delete_book(book_id: int) -> Response:
        if not repository.delete(book_id):
            raise _not_found(book_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return app
