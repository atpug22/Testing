from typing import Callable

from fastapi import APIRouter, Depends, HTTPException

from app.controllers.invitation import InvitationController
from app.controllers.organization import OrganizationController
from app.controllers.user import UserController
from app.models.invitation import Invitation, InvitationStatus
from app.models.organization import Organization, OrganizationRole, organization_members
from app.models.user import User
from app.schemas.requests.invitation import InvitationCreateRequest
from app.schemas.requests.organization import (
    OrganizationCreateRequest,
    OrganizationUpdateRequest,
    OrganizationMemberInviteRequest,
)
from app.schemas.responses.invitation import InvitationResponse
from app.schemas.responses.organization import (
    OrganizationResponse,
    OrganizationDetailResponse,
)
from core.factory import Factory
from core.fastapi.dependencies import AuthenticationRequired
from core.fastapi.dependencies.current_user import get_current_user
from sqlalchemy import select, insert
from core.database.session import session

organization_router = APIRouter()


@organization_router.get("/", dependencies=[Depends(AuthenticationRequired)])
async def get_organizations(
    user: User = Depends(get_current_user),
    organization_controller: OrganizationController = Depends(Factory().get_organization_controller),
) -> list[OrganizationResponse]:
    """Get all organizations for the current user"""
    organizations = await organization_controller.get_by_user(user.id)
    # Convert SQLAlchemy models to Pydantic models (Pydantic v1 uses from_orm)
    return [OrganizationResponse.from_orm(org) for org in organizations]


@organization_router.post("/", status_code=201)
async def create_organization(
    request: OrganizationCreateRequest,
    user: User = Depends(get_current_user),
    organization_controller: OrganizationController = Depends(Factory().get_organization_controller),
) -> OrganizationResponse:
    """Create a new organization"""
    # Check if organization name already exists
    existing_org = await organization_controller.get_by_name(request.name)
    if existing_org:
        raise HTTPException(status_code=400, detail="Organization name already exists")

    # Create organization
    organization = await organization_controller.create(
        {
            "name": request.name,
            "description": request.description,
            "owner_id": user.id,
        }
    )

    # Add owner as admin member
    from core.database.session import get_session
    
    async for db_session in get_session():
        try:
            # Insert into association table with role
            await db_session.execute(
                insert(organization_members).values(
                    user_id=user.id,
                    organization_id=organization.id,
                    role=OrganizationRole.ADMIN
                )
            )
            await db_session.commit()
            
            # Query the organization again to get a fresh object with proper session
            stmt = select(Organization).where(Organization.id == organization.id)
            result = await db_session.execute(stmt)
            fresh_org = result.scalar_one()
            
            # Use Pydantic's from_orm to convert SQLAlchemy model (Pydantic v1)
            return OrganizationResponse.from_orm(fresh_org)
        finally:
            await db_session.close()


@organization_router.get("/{organization_id}", dependencies=[Depends(AuthenticationRequired)])
async def get_organization(
    organization_id: int,
    user: User = Depends(get_current_user),
    organization_controller: OrganizationController = Depends(Factory().get_organization_controller),
) -> OrganizationDetailResponse:
    """Get organization details"""
    organization = await organization_controller.get_by_id(
        organization_id, join_={"members", "owner"}
    )
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Check if user is a member
    if user.id not in [member.id for member in organization.members]:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    
    return OrganizationDetailResponse.from_orm(organization)


@organization_router.patch("/{organization_id}", dependencies=[Depends(AuthenticationRequired)])
async def update_organization(
    organization_id: int,
    request: OrganizationUpdateRequest,
    user: User = Depends(get_current_user),
    organization_controller: OrganizationController = Depends(Factory().get_organization_controller),
) -> OrganizationResponse:
    """Update organization (admin only)"""
    organization = await organization_controller.get_by_id(organization_id)
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Check if user is admin
    # TODO: Check user role in organization
    if organization.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Only organization admin can update")
    
    # Update fields
    if request.name:
        organization.name = request.name
    if request.description is not None:
        organization.description = request.description
    
    updated_org = await organization_controller.update(id_=organization_id, obj=organization)
    return OrganizationResponse.from_orm(updated_org)


@organization_router.delete("/{organization_id}", dependencies=[Depends(AuthenticationRequired)])
async def delete_organization(
    organization_id: int,
    user: User = Depends(get_current_user),
    organization_controller: OrganizationController = Depends(Factory().get_organization_controller),
):
    """Delete organization (owner only)"""
    organization = await organization_controller.get_by_id(organization_id)
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    if organization.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Only organization owner can delete")
    
    await organization_controller.delete(id_=organization_id)
    return {"message": "Organization deleted successfully"}


@organization_router.post("/{organization_id}/invite", dependencies=[Depends(AuthenticationRequired)])
async def invite_member(
    organization_id: int,
    request: InvitationCreateRequest,
    user: User = Depends(get_current_user),
    organization_controller: OrganizationController = Depends(Factory().get_organization_controller),
    invitation_controller: InvitationController = Depends(Factory().get_invitation_controller),
) -> InvitationResponse:
    """Invite a member to the organization by email (admin only)"""
    organization = await organization_controller.get_by_id(organization_id)
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Check if user is admin (check organization_members table)
    stmt = select(organization_members.c.role).where(
        organization_members.c.organization_id == organization_id,
        organization_members.c.user_id == user.id
    )
    result = await session.execute(stmt)
    role = result.scalar_one_or_none()
    
    if role != OrganizationRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only organization admins can invite members")
    
    # Check if email is already a member
    stmt = select(User).where(User.email == request.email)
    result = await session.execute(stmt)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        # Check if already a member
        stmt = select(organization_members).where(
            organization_members.c.organization_id == organization_id,
            organization_members.c.user_id == existing_user.id
        )
        result = await session.execute(stmt)
        if result.first():
            raise HTTPException(status_code=400, detail="User is already a member of this organization")
    
    # Check if there's already a pending invitation
    pending_invitations = await invitation_controller.get_pending_by_email(request.email)
    for inv in pending_invitations:
        if inv.organization_id == organization_id:
            raise HTTPException(status_code=400, detail="An invitation is already pending for this email")
    
    # Create invitation
    invitation = await invitation_controller.create(
        Invitation(
            email=request.email,
            organization_id=organization_id,
            role=request.role,
            invited_by_id=user.id,
            expires_at=Invitation.create_expiry(days=7),
        )
    )
    
    return invitation


@organization_router.get("/{organization_id}/invitations", dependencies=[Depends(AuthenticationRequired)])
async def get_organization_invitations(
    organization_id: int,
    user: User = Depends(get_current_user),
    invitation_controller: InvitationController = Depends(Factory().get_invitation_controller),
) -> list[InvitationResponse]:
    """Get all invitations for an organization (admin only)"""
    # Check if user is admin
    stmt = select(organization_members.c.role).where(
        organization_members.c.organization_id == organization_id,
        organization_members.c.user_id == user.id
    )
    result = await session.execute(stmt)
    role = result.scalar_one_or_none()
    
    if role != OrganizationRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only organization admins can view invitations")
    
    invitations = await invitation_controller.get_by_organization(organization_id)
    return invitations

