"""Pytest configuration."""
import pytest
import os


def pytest_configure(config):
    """Configure pytest."""
    # Set test environment variables
    os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
    os.environ.setdefault("DEBUG", "true")
