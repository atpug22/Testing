from pydantic import BaseModel, Field


class OrganizationCreateRequest(BaseModel):
    """Request schema for creating an organization"""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=500)


class OrganizationUpdateRequest(BaseModel):
    """Request schema for updating an organization"""
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=500)


class OrganizationMemberInviteRequest(BaseModel):
    """Request schema for inviting a member to an organization"""
    user_id: int = Field(..., description="User ID to invite")
    role: str = Field(..., description="Role: admin or member")

