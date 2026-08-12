"""
Legal AI System - Authentication Router
=========================================
API endpoints for user registration, login, token refresh,
password reset, and profile management.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserProfileResponse,
    SendOTPRequest,
    VerifyOTPRequest,
    UpdateProfileRequest,
    ChangePasswordRequest,
    UpdateSettingsRequest
)
from app.api.common.responses import success_response
from app.core.security import get_current_user_token
from app.database.session import get_db
from app.services.auth_service import auth_service

router = APIRouter()

@router.post("/send-otp", response_model=dict)
async def send_otp(data: SendOTPRequest, db: AsyncSession = Depends(get_db)):
    """Send a 6-digit OTP to the user's email for verification."""
    result = await auth_service.send_registration_otp(db, data)
    return success_response(message=result["message"])

@router.post("/verify-otp", response_model=dict)
async def verify_otp(data: VerifyOTPRequest, db: AsyncSession = Depends(get_db)):
    """Verify the 6-digit OTP and return a temporary verification token."""
    result = await auth_service.verify_registration_otp(db, data)
    return success_response(
        message=result["message"],
        data={"verification_token": result["verification_token"]}
    )

@router.post("/register", response_model=dict, status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    result = await auth_service.register_user(db, data)
    return success_response(
        message="User registered successfully", data=result
    )


@router.post("/login", response_model=dict)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return tokens."""
    tokens = await auth_service.login_user(db, data)
    return success_response(message="Login successful", data=tokens)


@router.get("/me", response_model=dict)
async def get_current_user_profile(
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Get the currently logged in user's profile information."""
    from app.repositories.user_repository import user_repository
    user_id = token_data.get("sub")
    user = await user_repository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user_data = {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role.name if user.role else "client",
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "phone": user.phone,
        "preferences": user.preferences,
    }
    return success_response(message="Profile retrieved", data=user_data)


@router.put("/settings", response_model=dict)
async def update_settings(
    data: UpdateSettingsRequest,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Update user preferences/settings."""
    from app.repositories.user_repository import user_repository
    user_id = token_data.get("sub")
    user = await user_repository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    await user_repository.update(db, db_obj=user, obj_in={"preferences": data.preferences})
    
    return success_response(message="Settings updated successfully")


@router.put("/profile", response_model=dict)
async def update_profile(
    data: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Update current user profile information."""
    from app.repositories.user_repository import user_repository
    user_id = token_data.get("sub")
    user = await user_repository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    update_data = data.model_dump(exclude_unset=True)
    
    # User model doesn't have address, so we pop it if it was sent,
    # or handle it differently if we were saving it to a Profile table.
    if "address" in update_data:
        update_data.pop("address")
        
    if update_data:
        await user_repository.update(db, db_obj=user, obj_in=update_data)
    
    return success_response(message="Profile updated successfully")


@router.put("/change-password", response_model=dict)
async def change_password(
    data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    token_data: dict = Depends(get_current_user_token)
):
    """Change current user's password."""
    from app.repositories.user_repository import user_repository
    from app.core.security import verify_password, hash_password
    from app.core.exceptions import BadRequestException
    
    user_id = token_data.get("sub")
    user = await user_repository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if not verify_password(data.current_password, user.password_hash):
        raise BadRequestException(message="Incorrect current password")
        
    new_hashed_password = hash_password(data.new_password)
    await user_repository.update(db, db_obj=user, obj_in={"password_hash": new_hashed_password})
    
    return success_response(message="Password changed successfully")


@router.post("/refresh", response_model=dict)
async def refresh_token(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """
    Refresh an expired access token using a valid refresh token.
    
    - Validates refresh_token
    - Issues new access_token
    - Rotates refresh_token
    """
    tokens = await auth_service.refresh_token_user(db, data.refresh_token)
    return success_response(
        message="Token refreshed successfully",
        data=tokens
    )


@router.post("/forgot-password", response_model=dict)
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    Request a password reset email.
    
    - Generates reset token
    - Sends email with reset link
    """
    result = await auth_service.send_password_reset_email(db, data.email)
    return success_response(
        message=result["message"]
    )


@router.post("/reset-password", response_model=dict)
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    Reset password using a valid reset token.
    
    - Validates reset token
    - Updates password hash
    - Invalidates reset token
    """
    result = await auth_service.reset_password(db, data.token, data.new_password)
    return success_response(
        message=result["message"]
    )





@router.post("/logout", response_model=dict)
async def logout(
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout user by invalidating refresh token.
    
    Requires: Valid JWT access token in Authorization header.
    """
    user_id = token_data.get("sub")
    if user_id:
        await auth_service.logout_user(db, user_id)
        
    return success_response(
        message="Logout successful",
    )
