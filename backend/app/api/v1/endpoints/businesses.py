import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.business import Business, BusinessMembership
from app.schemas.business import (
    BusinessCreate,
    BusinessRead,
    BusinessUpdate,
    BusinessMemberCreate,
    BusinessMemberWithUserRead,
)
from app.api.deps import get_current_user, get_current_business, require_business_role

router = APIRouter()


@router.post("/", response_model=BusinessRead, status_code=status.HTTP_201_CREATED, summary="Create a new business workspace")
def create_business(
    business_in: BusinessCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Business:
    """Create a new business workspace and make current user the owner."""
    existing = db.query(Business).filter(Business.slug == business_in.slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Business slug '{business_in.slug}' is already taken",
        )

    business = Business(
        name=business_in.name,
        slug=business_in.slug,
        legal_name=business_in.legal_name,
        tax_id=business_in.tax_id,
        currency=business_in.currency or "BDT",
        phone=business_in.phone,
        email=business_in.email,
        address=business_in.address,
        is_active=True,
    )
    db.add(business)
    db.flush()

    # Automatically add creator as 'owner'
    membership = BusinessMembership(
        business_id=business.id,
        user_id=current_user.id,
        role="owner",
        is_active=True,
    )
    db.add(membership)
    db.commit()
    db.refresh(business)
    return business


@router.get("/", response_model=List[BusinessRead], summary="List business workspaces current user belongs to")
def list_my_businesses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Business]:
    """Retrieve all business workspaces where the user is an active member."""
    businesses = (
        db.query(Business)
        .join(BusinessMembership, Business.id == BusinessMembership.business_id)
        .filter(
            BusinessMembership.user_id == current_user.id,
            BusinessMembership.is_active.is_(True),
            Business.is_active.is_(True),
        )
        .all()
    )
    return businesses


@router.get("/{business_id}", response_model=BusinessRead, summary="Get business workspace details")
def get_business_details(
    business: Business = Depends(get_current_business),
) -> Business:
    """Get business details. Accessible only to verified members."""
    return business


@router.put("/{business_id}", response_model=BusinessRead, summary="Update business workspace details")
def update_business(
    business_in: BusinessUpdate,
    business: Business = Depends(require_business_role("owner", "accountant")),
    db: Session = Depends(get_db),
) -> Business:
    """Update business details. Requires owner or accountant role."""
    update_data = business_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(business, field, val)

    db.commit()
    db.refresh(business)
    return business


@router.get("/{business_id}/members", response_model=List[BusinessMemberWithUserRead], summary="List business workspace members")
def list_business_members(
    business: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> List[BusinessMemberWithUserRead]:
    """List members of this business workspace. Accessible only to members."""
    memberships = (
        db.query(BusinessMembership, User)
        .join(User, BusinessMembership.user_id == User.id)
        .filter(
            BusinessMembership.business_id == business.id,
            BusinessMembership.is_active.is_(True),
        )
        .all()
    )

    result = []
    for m, u in memberships:
        result.append(
            BusinessMemberWithUserRead(
                id=m.id,
                business_id=m.business_id,
                user_id=u.id,
                email=u.email,
                full_name=u.full_name,
                role=m.role,
                is_active=m.is_active,
                created_at=m.created_at,
            )
        )
    return result


@router.post("/{business_id}/members", response_model=BusinessMemberWithUserRead, status_code=status.HTTP_201_CREATED, summary="Add a member to business workspace")
def add_business_member(
    member_in: BusinessMemberCreate,
    business: Business = Depends(require_business_role("owner")),
    db: Session = Depends(get_db),
) -> BusinessMemberWithUserRead:
    """Add a user to this business. Restricted to owners."""
    target_user = db.query(User).filter(User.email == member_in.email.lower()).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email '{member_in.email}' not found. The user must register first.",
        )

    existing_membership = (
        db.query(BusinessMembership)
        .filter(
            BusinessMembership.business_id == business.id,
            BusinessMembership.user_id == target_user.id,
        )
        .first()
    )

    if existing_membership:
        if existing_membership.is_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already an active member of this business",
            )
        else:
            # Reactivate membership with new role
            existing_membership.is_active = True
            existing_membership.role = member_in.role
            db.commit()
            db.refresh(existing_membership)
            return BusinessMemberWithUserRead(
                id=existing_membership.id,
                business_id=business.id,
                user_id=target_user.id,
                email=target_user.email,
                full_name=target_user.full_name,
                role=existing_membership.role,
                is_active=True,
                created_at=existing_membership.created_at,
            )

    membership = BusinessMembership(
        business_id=business.id,
        user_id=target_user.id,
        role=member_in.role,
        is_active=True,
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)

    return BusinessMemberWithUserRead(
        id=membership.id,
        business_id=business.id,
        user_id=target_user.id,
        email=target_user.email,
        full_name=target_user.full_name,
        role=membership.role,
        is_active=True,
        created_at=membership.created_at,
    )
