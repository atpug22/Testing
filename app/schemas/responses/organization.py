from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


class OrganizationMemberResponse(BaseModel):
    """Response schema for organization member"""
    id: int
    username: str
    email: str
    role: str

    class Config:
        orm_mode = True  # Pydantic v1 syntax


class OrganizationResponse(BaseModel):
    """Response schema for organization"""
    id: int
    uuid: UUID
    name: str
    description: str | None
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True  # Pydantic v1 syntax


class OrganizationDetailResponse(OrganizationResponse):
    """Detailed response schema for organization with members"""
    members: list[OrganizationMemberResponse] = []

    class Config:
        orm_mode = True  # Pydantic v1 syntax

