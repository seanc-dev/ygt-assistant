"""Factory for Nylas grants repository."""

from infra.repos.nylas_grants_repo import NylasGrantsRepo


def repo() -> NylasGrantsRepo:
    """Get Nylas grants repository instance."""
    return NylasGrantsRepo()
