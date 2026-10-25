"""Bookstore API: the system under test for the contract and functional suites."""

from bookstore.app import create_app

__version__ = "1.0.0"

__all__ = ["__version__", "create_app"]
