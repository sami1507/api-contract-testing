"""Request and response models. These definitions are the source of the OpenAPI contract."""

from __future__ import annotations

import re
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

ISBN13_PATTERN = r"^97[89]\d{10}$"
_ISBN13_RE = re.compile(ISBN13_PATTERN)


def isbn13_check_digit(prefix: str) -> str:
    """Compute the ISBN-13 check digit for the first twelve digits."""
    total = sum(int(digit) * (1 if index % 2 == 0 else 3) for index, digit in enumerate(prefix))
    return str((10 - total % 10) % 10)


def make_isbn13(prefix: str) -> str:
    """Append the correct check digit to a twelve-digit prefix."""
    return prefix + isbn13_check_digit(prefix)


def is_valid_isbn13(isbn: str) -> bool:
    return bool(_ISBN13_RE.match(isbn)) and isbn[-1] == isbn13_check_digit(isbn[:-1])


class Genre(str, Enum):
    FICTION = "fiction"
    SCIENCE = "science"
    HISTORY = "history"
    TECHNOLOGY = "technology"
    POETRY = "poetry"


class BookCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200, examples=["Designing Quiet Systems"])
    author: str = Field(min_length=1, max_length=120, examples=["Lena Park"])
    isbn: str = Field(pattern=ISBN13_PATTERN, examples=["9780000000019"])
    genre: Genre
    year: int = Field(ge=1450, le=2100)
    price: float = Field(gt=0, le=10_000)

    @field_validator("isbn")
    @classmethod
    def check_isbn_checksum(cls, value: str) -> str:
        if not is_valid_isbn13(value):
            raise ValueError("invalid ISBN-13 check digit")
        return value


class BookUpdate(BaseModel):
    """Partial update. The ISBN is deliberately not updatable, so it is not listed here."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=200)
    author: str | None = Field(default=None, min_length=1, max_length=120)
    genre: Genre | None = None
    year: int | None = Field(default=None, ge=1450, le=2100)
    price: float | None = Field(default=None, gt=0, le=10_000)


class Book(BookCreate):
    id: int = Field(ge=1)


class BookPage(BaseModel):
    items: list[Book]
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
