from typing import Protocol, Dict, Any


class CRMPort(Protocol):
    """Port interface for CRM providers."""

    def upsert_contact(self, details: Dict[str, Any], *, dry_run: bool = True) -> Dict[str, Any]:
        """Create or update a contact record with the given details."""

        ...


