"""HTTP layer — a thin FastAPI adapter around the `pricecompare` core.

This package owns transport concerns only (routing, JSON, static files). All
business logic lives in the framework-agnostic `pricecompare` package.
"""
