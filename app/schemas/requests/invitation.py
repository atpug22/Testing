from pydantic import BaseModel, Field, EmailStr


class InvitationCreateRequest(BaseModel):
    """Request schema for creating an invitation"""
    email: EmailStr = Field(..., description="Email address to invite")
    role: str = Field(..., description="Role: admin or member")


class InvitationResponseRequest(BaseModel):
    """Request schema for responding to an invitation"""
    accept: bool = Field(..., description="Accept or decline the invitation")

