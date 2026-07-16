"""Authentication routes for signup and login."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models import User

router = APIRouter(prefix="/auth", tags=["authentication"])


class SignupRequest(BaseModel):
    """Request model for user signup."""

    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    """Request model for user login."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str
    email: str


@router.post("/signup", response_model=TokenResponse)
async def signup(
    request: SignupRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user and return JWT token.

    - **email**: User email address
    - **password**: User password (hashed with Argon2)
    """
    # Check if user already exists
    stmt = select(User).where(User.email == request.email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    hashed_pwd = hash_password(request.password)
    user = User(email=request.email, hashed_password=hashed_pwd)

    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Generate token
    access_token = create_access_token(data={"sub": user.email})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        email=user.email,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Login user and return JWT token.

    - **email**: User email address
    - **password**: User password
    """
    # Find user
    stmt = select(User).where(User.email == request.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Verify password
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Generate token
    access_token = create_access_token(data={"sub": user.email})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        email=user.email,
    )
