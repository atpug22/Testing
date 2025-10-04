from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


class OrganizationMemberResponse(BaseModel):
    """Response schema for organization member"""
    id: int
    username: str
    email: str
    role: str

    model_config = {"from_attributes": True}  # Pydantic v2 syntax


class OrganizationResponse(BaseModel):
    """Response schema for organization"""
    id: int
    uuid: UUID
    name: str
    description: str | None
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}  # Pydantic v2 syntax


class OrganizationDetailResponse(OrganizationResponse):
    """Detailed response schema for organization with members"""
    members: list[OrganizationMemberResponse] = []

    model_config = {"from_attributes": True}  # Pydantic v2 syntax

