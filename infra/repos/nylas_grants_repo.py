"""Repository for Nylas grant persistence."""

import json
import os
from typing import List, Optional
from datetime import datetime

from core.domain.nylas_grant import NylasGrant


class NylasGrantsRepo:
    """Repository for managing Nylas OAuth grants."""
    
    def __init__(self, file_path: str = "nylas_grants.json"):
        """Initialize with file path for persistence."""
        self.file_path = file_path
        self._ensure_file()
    
    def _ensure_file(self):
        """Ensure the grants file exists."""
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as f:
                json.dump([], f)
    
    def _load_grants(self) -> List[NylasGrant]:
        """Load all grants from file."""
        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
            return [NylasGrant.from_dict(grant) for grant in data]
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_grants(self, grants: List[NylasGrant]):
        """Save all grants to file."""
        with open(self.file_path, "w") as f:
            json.dump([grant.to_dict() for grant in grants], f, indent=2)
    
    def create(self, grant: NylasGrant) -> NylasGrant:
        """Create a new grant."""
        grants = self._load_grants()
        
        # Set timestamps
        now = datetime.now()
        grant.created_at = now
        grant.updated_at = now
        
        grants.append(grant)
        self._save_grants(grants)
        return grant
    
    def get_by_grant_id(self, grant_id: str) -> Optional[NylasGrant]:
        """Get grant by grant_id."""
        grants = self._load_grants()
        for grant in grants:
            if grant.grant_id == grant_id:
                return grant
        return None
    
    def get_by_email(self, email: str) -> List[NylasGrant]:
        """Get all grants for an email address."""
        grants = self._load_grants()
        return [grant for grant in grants if grant.email == email]
    
    def get_by_provider(self, provider: str) -> List[NylasGrant]:
        """Get all grants for a provider."""
        grants = self._load_grants()
        return [grant for grant in grants if grant.provider == provider]
    
    def update(self, grant_id: str, **updates) -> Optional[NylasGrant]:
        """Update a grant by grant_id."""
        grants = self._load_grants()
        for i, grant in enumerate(grants):
            if grant.grant_id == grant_id:
                # Update fields
                for key, value in updates.items():
                    if hasattr(grant, key):
                        setattr(grant, key, value)
                
                grant.updated_at = datetime.now()
                grants[i] = grant
                self._save_grants(grants)
                return grant
        return None
    
    def delete(self, grant_id: str) -> bool:
        """Delete a grant by grant_id."""
        grants = self._load_grants()
        original_count = len(grants)
        grants = [grant for grant in grants if grant.grant_id != grant_id]
        
        if len(grants) < original_count:
            self._save_grants(grants)
            return True
        return False
    
    def list_all(self) -> List[NylasGrant]:
        """List all grants."""
        return self._load_grants()
