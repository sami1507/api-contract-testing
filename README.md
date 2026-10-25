# api-contract-testing

[![API tests](https://github.com/sami1507/api-contract-testing/actions/workflows/api-tests.yml/badge.svg)](https://github.com/sami1507/api-contract-testing/actions/workflows/api-tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![pytest](https://img.shields.io/badge/tested%20with-pytest-0A9EDC)

A pytest suite for a REST API. It checks that the implementation matches its OpenAPI contract, that the main flows work end to end, that bad input is rejected with clear messages, that write operations are protected, and that reads stay within a latency budget.

The system under test is a small bookstore API built with FastAPI. It runs in-process through `TestClient`, so the suite needs no server, no database and no network access, and it runs in a few seconds.

## What the suite checks

| Layer          | Marker       | What it proves                                                                  |
| -------------- | ------------ | ------------------------------------------------------------------------------- |
| Smoke          | `smoke`      | The service is up, the catalogue is seeded, and the health endpoint works        |
| Contract       | `contract`   | Every response validates against the schema in `/openapi.json`; error bodies follow the documented shape |
| Functional     | (none)       | CRUD flows, pagination, genre filtering, `Location` headers, ISBN reuse after delete |
| Negative       | `negative`   | Invalid fields, wrong ISBN check digit, unknown fields, out-of-range query parameters |
| Auth           | `auth`       | Writes need `X-API-Key`; wrong keys and keys in the query string are refused     |
| Performance    | `performance`| The list endpoint answers within the latency budget                             |

The contract tests use the API's own generated OpenAPI document as the source of truth. When a model changes, the response schemas change with it, and the tests keep following the contract instead of hard-coded expectations.

## Quick start

```bash
python -m pip install -e ".[dev]"

pytest                  # everything
pytest -m smoke         # fast gate for a deployment
pytest -m contract      # contract checks only
pytest -m "auth or negative"
ruff check .
```

Reports for CI are written as JUnit XML with `pytest --junitxml=test-results/junit.xml`.

## Example: what a contract failure looks like

If a field's constraints drift from what the API promises, the contract test fails with the offending schema path, for example:

```text
FAILED tests/contract/test_openapi_contract.py::test_book_schema_publishes_the_validation_rules
    assert schema["year"]["maximum"] == 2100
    KeyError: 'maximum'
```

## Project layout

```text
src/bookstore/
  models.py       Pydantic models, ISBN-13 check-digit rule
  store.py        Thread-safe in-memory repository
  seed.py         Demo catalogue with valid ISBNs
  app.py          FastAPI routes and API-key dependency
tests/
  conftest.py     Fresh API per test, auth headers, valid payload factory
  contract/       OpenAPI document and response schema checks
  functional/     CRUD flows, pagination, filters, latency budget
  negative/       Validation rules, one parametrised case per rule
  auth/           API key enforcement on every write operation
```

## Design notes

- **Fresh state per test.** Each test builds its own store from the seed data, so tests can run in any order and in parallel.
- **Schema-driven contract checks.** Responses are validated with `jsonschema` against `app.openapi()`, which means the documentation itself is tested.
- **One rule, one case.** Validation cases are parametrised with readable `ids`, so a failing rule is named directly in the output.
- **Checksums in the test data.** Test ISBNs are built with `make_isbn13`, so the valid and invalid cases are generated from the same rule the server enforces.

## Continuous integration

`.github/workflows/api-tests.yml` lints the project and runs the smoke tests before the full suite on Python 3.10, 3.12 and 3.13. JUnit results are uploaded as artifacts.

## Tech stack

Python · FastAPI · Pydantic · pytest · jsonschema · httpx · ruff · GitHub Actions

## License

MIT. See [LICENSE](LICENSE).
