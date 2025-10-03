"""
Script to seed an organization for existing users.
This helps with the initial setup after adding the organization feature.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select, insert
from app.models import User, Organization
from app.models.organization import OrganizationRole, organization_members
from core.database import standalone_session, session


@standalone_session
async def seed_organization():
    """Create a default organization for existing users"""
    async with session.begin():
        try:
            # Get all users
            stmt = select(User)
            result = await session.execute(stmt)
            users = result.scalars().all()
            
            if not users:
                print("No users found. Please create a user first.")
                return
            
            # Create a default organization for the first user
            first_user = users[0]
            
            # Check if organization already exists
            org_stmt = select(Organization).where(Organization.owner_id == first_user.id)
            result = await session.execute(org_stmt)
            existing_org = result.scalar_one_or_none()
            
            if existing_org:
                print(f"Organization '{existing_org.name}' already exists for user {first_user.username}")
                return
            
            # Create organization
            org = Organization(
                name=f"{first_user.username}'s Organization",
                description="Default organization",
                owner_id=first_user.id,
            )
            session.add(org)
            await session.flush()
            
            # Add owner as admin member
            await session.execute(
                insert(organization_members).values(
                    user_id=first_user.id,
                    organization_id=org.id,
                    role=OrganizationRole.ADMIN
                )
            )
            
            print(f"✅ Created organization '{org.name}' for user {first_user.username}")
            print(f"   Organization ID: {org.id}")
            print(f"   User role: ADMIN")
            
        except Exception as e:
            print(f"❌ Error creating organization: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_organization())

