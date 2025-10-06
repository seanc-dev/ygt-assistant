"""Nylas grant domain model for OAuth token persistence."""

from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class NylasGrant:
    """Represents a Nylas OAuth grant for a provider account."""
    
    grant_id: str
    provider: str  # "google" or "microsoft"
    email: str
    scopes: List[str]
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            "grant_id": self.grant_id,
            "provider": self.provider,
            "email": self.email,
            "scopes": self.scopes,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "NylasGrant":
        """Create from dictionary."""
        return cls(
            grant_id=data["grant_id"],
            provider=data["provider"],
            email=data["email"],
            scopes=data["scopes"],
            access_token=data.get("access_token"),
            refresh_token=data.get("refresh_token"),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )
