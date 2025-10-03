from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from app.controllers.invitation import InvitationController
from app.controllers.organization import OrganizationController
from app.models.invitation import InvitationStatus
from app.models.organization import organization_members
from app.models.user import User
from app.schemas.responses.invitation import InvitationWithOrgResponse
from core.factory import Factory
from core.fastapi.dependencies import AuthenticationRequired
from core.fastapi.dependencies.current_user import get_current_user
from sqlalchemy import insert
from core.database.session import session

invitation_router = APIRouter()


@invitation_router.get("/me", dependencies=[Depends(AuthenticationRequired)])
async def get_my_invitations(
    user: User = Depends(get_current_user),
    invitation_controller: InvitationController = Depends(Factory().get_invitation_controller),
) -> list[InvitationWithOrgResponse]:
    """Get pending invitations for the current user's email"""
    invitations = await invitation_controller.get_pending_by_email(
        user.email, join_={"organization", "invited_by"}
    )
    
    # Convert to response with organization details
    result = []
    for inv in invitations:
        # Check if invitation is still valid (not expired)
        if not inv.is_valid():
            continue
            
        result.append(
            InvitationWithOrgResponse(
                id=inv.id,
                uuid=inv.uuid,
                email=inv.email,
                organization_id=inv.organization_id,
                organization_name=inv.organization.name,
                role=inv.role,
                status=inv.status.value,
                expires_at=inv.expires_at,
                created_at=inv.created_at,
                invited_by_username=inv.invited_by.username if inv.invited_by else None,
            )
        )
    
    return result


@invitation_router.post("/{invitation_id}/accept", dependencies=[Depends(AuthenticationRequired)])
async def accept_invitation(
    invitation_id: int,
    user: User = Depends(get_current_user),
    invitation_controller: InvitationController = Depends(Factory().get_invitation_controller),
):
    """Accept an invitation to join an organization"""
    invitation = await invitation_controller.get_by_id(invitation_id)
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    # Verify the invitation is for this user's email
    if invitation.email != user.email:
        raise HTTPException(status_code=403, detail="This invitation is not for you")
    
    # Check if invitation is valid
    if not invitation.is_valid():
        raise HTTPException(status_code=400, detail="Invitation is no longer valid or has expired")
    
    # Check if user is already a member
    from sqlalchemy import select
    stmt = select(organization_members).where(
        organization_members.c.organization_id == invitation.organization_id,
        organization_members.c.user_id == user.id
    )
    result = await session.execute(stmt)
    if result.first():
        raise HTTPException(status_code=400, detail="You are already a member of this organization")
    
    # Add user to organization
    await session.execute(
        insert(organization_members).values(
            user_id=user.id,
            organization_id=invitation.organization_id,
            role=invitation.role
        )
    )
    
    # Update invitation status
    invitation.status = InvitationStatus.ACCEPTED
    invitation.responded_at = datetime.utcnow()
    await invitation_controller.update(id_=invitation_id, obj=invitation)
    
    await session.commit()
    
    return {"message": "Invitation accepted successfully"}


@invitation_router.post("/{invitation_id}/decline", dependencies=[Depends(AuthenticationRequired)])
async def decline_invitation(
    invitation_id: int,
    user: User = Depends(get_current_user),
    invitation_controller: InvitationController = Depends(Factory().get_invitation_controller),
):
    """Decline an invitation to join an organization"""
    invitation = await invitation_controller.get_by_id(invitation_id)
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    # Verify the invitation is for this user's email
    if invitation.email != user.email:
        raise HTTPException(status_code=403, detail="This invitation is not for you")
    
    # Check if invitation is valid
    if invitation.status != InvitationStatus.PENDING:
        raise HTTPException(status_code=400, detail="Invitation has already been responded to")
    
    # Update invitation status
    invitation.status = InvitationStatus.DECLINED
    invitation.responded_at = datetime.utcnow()
    await invitation_controller.update(id_=invitation_id, obj=invitation)
    
    return {"message": "Invitation declined"}

