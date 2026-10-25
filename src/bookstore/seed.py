"""Demo catalogue loaded when the API starts. Every ISBN is generated with a valid check digit."""

from bookstore.models import BookCreate, Genre, make_isbn13


def seed_books() -> list[BookCreate]:
    return [
        BookCreate(
            title="Designing Quiet Systems",
            author="Lena Park",
            isbn=make_isbn13("978000000001"),
            genre=Genre.TECHNOLOGY,
            year=2019,
            price=44.9,
        ),
        BookCreate(
            title="A Short History of Tea",
            author="Omar Haddad",
            isbn=make_isbn13("978000000002"),
            genre=Genre.HISTORY,
            year=2008,
            price=18.5,
        ),
        BookCreate(
            title="Field Notes on Glaciers",
            author="Ingrid Solberg",
            isbn=make_isbn13("978000000003"),
            genre=Genre.SCIENCE,
            year=2014,
            price=27.0,
        ),
        BookCreate(
            title="Lanterns Over Dunes",
            author="Amara Diallo",
            isbn=make_isbn13("978000000004"),
            genre=Genre.POETRY,
            year=2021,
            price=12.75,
        ),
        BookCreate(
            title="The Clockmaker's Ledger",
            author="Peter Vance",
            isbn=make_isbn13("978000000005"),
            genre=Genre.FICTION,
            year=2016,
            price=15.99,
        ),
        BookCreate(
            title="Practical Load Testing",
            author="Mei Lin",
            isbn=make_isbn13("978000000006"),
            genre=Genre.TECHNOLOGY,
            year=2023,
            price=39.95,
        ),
    ]
