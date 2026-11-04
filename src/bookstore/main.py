"""ASGI entry point for running the API: `uvicorn bookstore.main:app`.

Set BOOKSTORE_API_KEY to change the key that protects write operations.
"""

import os

from bookstore.app import DEFAULT_API_KEY, create_app

app = create_app(api_key=os.environ.get("BOOKSTORE_API_KEY", DEFAULT_API_KEY))
