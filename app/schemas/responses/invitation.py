from datetime import datetime
from pydantic import BaseModel
from uuid import UUID


class InvitationResponse(BaseModel):
    """Response schema for invitation"""
    id: int
    uuid: UUID
    email: str
    organization_id: int
    role: str
    status: str
    expires_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class InvitationWithOrgResponse(BaseModel):
    """Response schema for invitation with organization details"""
    id: int
    uuid: UUID
    email: str
    organization_id: int
    organization_name: str
    role: str
    status: str
    expires_at: datetime
    created_at: datetime
    invited_by_username: str | None

    model_config = {"from_attributes": True}

