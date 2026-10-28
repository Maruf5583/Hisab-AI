import uuid
from typing import Generator, Optional, List
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.security import decode_access_token
from app.models.user import User
from app.models.business import Business, BusinessMembership

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=True,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    user_id_str: Optional[str] = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception
    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_uuid).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )
    return user


class BusinessTenantChecker:
    """Dependency that ensures the authenticated user is an authorized active member of the requested business."""

    def __init__(self, allowed_roles: Optional[List[str]] = None):
        self.allowed_roles = allowed_roles

    def __call__(
        self,
        business_id: uuid.UUID,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Business:
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business or not business.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business not found",
            )

        membership = (
            db.query(BusinessMembership)
            .filter(
                BusinessMembership.business_id == business_id,
                BusinessMembership.user_id == current_user.id,
                BusinessMembership.is_active.is_(True),
            )
            .first()
        )

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this business workspace",
            )

        if self.allowed_roles and membership.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action requires one of the following roles: {', '.join(self.allowed_roles)}",
            )

        return business


def get_current_business(
    business_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Business:
    checker = BusinessTenantChecker()
    return checker(business_id=business_id, current_user=current_user, db=db)


def get_active_business(
    x_business_id: Optional[str] = Header(None, alias="X-Business-Id"),
    business_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Business:
    target_id = None
    if business_id:
        target_id = business_id
    elif x_business_id:
        try:
            target_id = uuid.UUID(x_business_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid X-Business-Id UUID format",
            )
    else:
        memberships = (
            db.query(BusinessMembership)
            .filter(
                BusinessMembership.user_id == current_user.id,
                BusinessMembership.is_active.is_(True),
            )
            .all()
        )
        if len(memberships) == 1:
            target_id = memberships[0].business_id
        elif len(memberships) > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Multiple businesses found. Please specify X-Business-Id header or business_id query parameter.",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active business workspace found for user. Create a business first.",
            )

    checker = BusinessTenantChecker()
    return checker(business_id=target_id, current_user=current_user, db=db)


def require_business_role(*roles: str):
    return BusinessTenantChecker(allowed_roles=list(roles))

