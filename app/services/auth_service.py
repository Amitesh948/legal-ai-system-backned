"""
Legal AI System - Authentication Service
==========================================
Handles business logic for user registration, login, and token management.
"""

from typing import Dict, Any

import random
import string
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
from app.config import get_settings

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    UnauthorizedException,
)
from app.models.user import User
from app.repositories.user_repository import user_repository
from app.repositories.role_repository import role_repository
from app.repositories.otp_repository import otp_repository
from app.api.v1.auth.schemas import LoginRequest, RegisterRequest, SendOTPRequest, VerifyOTPRequest

settings = get_settings()

class AuthService:
    """Service layer for authentication operations."""

    @staticmethod
    async def send_registration_otp(db: AsyncSession, data: SendOTPRequest) -> dict:
        # Check if email is already registered
        existing_user = await user_repository.get_by_email(db, data.email)
        if existing_user:
            raise ConflictException(message="Email is already registered")

        # Generate 6-digit OTP
        otp_code = ''.join(random.choices(string.digits, k=6))
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        # Invalidate old OTPs for this email (or just rely on the newest one via order_by)
        otp_data = {
            "email": data.email,
            "otp_code": otp_code,
            "expires_at": expires_at
        }
        await otp_repository.create(db, otp_data)

        # Print to console as backup during dev
        print(f"\n{'='*40}\n[LOCAL DEV ONLY] Registration OTP for {data.email}: {otp_code}\n{'='*40}\n")

        # Send the email using aiosmtplib
        if settings.smtp_user and settings.smtp_password:
            from email.message import EmailMessage
            import aiosmtplib
            
            message = EmailMessage()
            message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
            message["To"] = data.email
            message["Subject"] = "Your Legal AI System Verification Code"
            
            message.set_content(f"""
            Hello,
            
            Your email verification code for the Legal AI System is: {otp_code}
            
            This code will expire in 10 minutes.
            
            If you did not request this, please ignore this email.
            """)
            
            try:
                await aiosmtplib.send(
                    message,
                    hostname=settings.smtp_host,
                    port=settings.smtp_port,
                    start_tls=True,
                    username=settings.smtp_user,
                    password=settings.smtp_password,
                )
            except Exception as e:
                print(f"Failed to send email: {e}")
                # We do not raise an exception to the user here to avoid blocking them if SMTP fails,
                # but in production, we should log this properly.

        return {"message": "OTP sent successfully to your email."}

    @staticmethod
    async def verify_registration_otp(db: AsyncSession, data: VerifyOTPRequest) -> dict:
        otp_record = await otp_repository.get_by_email(db, data.email)
        if not otp_record:
            raise BadRequestException(message="No OTP found for this email.")

        if otp_record.is_expired():
            raise BadRequestException(message="OTP has expired. Please request a new one.")

        if otp_record.otp_code != data.otp_code:
            raise BadRequestException(message="Invalid OTP code.")

        # Mark as verified
        await otp_repository.update(db, db_obj=otp_record, obj_in={"is_verified": True})

        # Generate a short-lived Verification Token to allow registration
        verification_payload = {
            "sub": data.email,
            "type": "verification",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15)
        }
        verification_token = jwt.encode(verification_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

        return {
            "message": "Email verified successfully.",
            "verification_token": verification_token
        }

    @staticmethod
    async def register_user(db: AsyncSession, data: RegisterRequest) -> dict:
        # Verify the verification_token
        try:
            payload = jwt.decode(data.verification_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            if payload.get("type") != "verification" or payload.get("sub") != data.email:
                raise UnauthorizedException(message="Invalid verification token for this email.")
        except JWTError:
            raise UnauthorizedException(message="Verification token is invalid or expired.")

        # 1. Check if user already exists
        existing_user = await user_repository.get_by_email(db, data.email)
        if existing_user:
            raise ConflictException(
                message="Registration failed",
                errors=[{"field": "email", "message": "Email is already registered"}],
            )

        # 2. Fetch the role
        role = await role_repository.get_by_name(db, data.role)
        if not role:
            role = await role_repository.create(db, {"name": data.role})

        # 3. Hash password and create user
        user_data = {
            "email": data.email,
            "password_hash": hash_password(data.password),
            "first_name": data.first_name,
            "last_name": data.last_name,
            "phone": data.phone,
            "role_id": role.id,
            "is_verified": True  # Since they verified via OTP
        }
        
        user = await user_repository.create(db, user_data)
        
        # 4. Send Welcome Email
        import asyncio
        from app.services.email_service import email_service
        asyncio.create_task(
            email_service.send_welcome_email(
                to_email=user.email,
                name=user.first_name,
                role=data.role
            )
        )
        
        return {
            "id": str(user.id),
            "email": user.email,
            "role": role.name,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }

    @staticmethod
    async def login_user(db: AsyncSession, data: LoginRequest) -> Dict[str, Any]:
        """
        Authenticate a user and generate JWT tokens.
        - Verifies email and password
        - Generates access and refresh tokens
        - Saves refresh token hash in DB for rotation
        """
        # 1. Find user by email
        user = await user_repository.get_by_email(db, data.email)
        if not user or not user.is_active:
            raise UnauthorizedException(message="Invalid email or password")

        # 2. Verify password
        if not verify_password(data.password, user.password_hash):
            raise UnauthorizedException(message="Invalid email or password")

        # 3. Generate tokens
        # We need the role name, which is a relationship. 
        # The repository uses lazy="selectin" so user.role is available.
        token_payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.name if user.role else "client",
        }

        access_token = create_access_token(token_payload)
        refresh_token = create_refresh_token(token_payload)

        # 4. Save refresh token in DB (hashed for security)
        # We hash it so if the DB is compromised, attackers can't use the refresh tokens
        hashed_refresh = hash_password(refresh_token)
        await user_repository.update(db, db_obj=user, obj_in={"refresh_token": hashed_refresh})

        # 5. Create Audit Log
        from app.models.audit_log import AuditLog
        db.add(AuditLog(
            user_id=user.id,
            action="LOGIN",
            resource_type="auth",
            resource_id=user.id,
            new_values={"details": f"User {user.email} logged in successfully."}
        ))
        await db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 15 * 60, # 15 minutes
        }

    @staticmethod
    async def refresh_token_user(db: AsyncSession, refresh_token_raw: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.
        - Verifies refresh token signature
        - Looks up user
        - Verifies refresh token hash in DB
        - Issues new access and refresh tokens
        """
        try:
            payload = jwt.decode(refresh_token_raw, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            if payload.get("type") != "refresh":
                raise UnauthorizedException(message="Invalid token type")
            user_id = payload.get("sub")
        except JWTError:
            raise UnauthorizedException(message="Refresh token is invalid or expired")

        user = await user_repository.get_by_id(db, user_id)
        if not user or not user.is_active or not user.refresh_token:
            raise UnauthorizedException(message="Invalid session")

        if not verify_password(refresh_token_raw, user.refresh_token):
            raise UnauthorizedException(message="Invalid refresh token")

        token_payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.name if user.role else "client",
        }

        new_access_token = create_access_token(token_payload)
        new_refresh_token = create_refresh_token(token_payload)

        hashed_refresh = hash_password(new_refresh_token)
        await user_repository.update(db, db_obj=user, obj_in={"refresh_token": hashed_refresh})

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": settings.jwt_access_token_expire_minutes * 60,
        }

    @staticmethod
    async def logout_user(db: AsyncSession, user_id: str) -> None:
        """
        Logout a user by invalidating their refresh token.
        """
        user = await user_repository.get_by_id(db, user_id)
        if user:
            await user_repository.update(db, db_obj=user, obj_in={"refresh_token": None})

    @staticmethod
    async def send_password_reset_email(db: AsyncSession, email: str) -> dict:
        """
        Generates a password reset token and sends it via email.
        """
        user = await user_repository.get_by_email(db, email)
        if not user:
            # We don't want to leak whether an email exists, so we return success anyway
            return {"message": "If an account exists, a reset link has been sent to the email."}
            
        # Generate a reset token (JWT)
        reset_payload = {
            "sub": str(user.id),
            "type": "reset",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30)
        }
        reset_token = jwt.encode(reset_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        
        # Log for dev purposes
        print(f"\n{'='*40}\n[LOCAL DEV ONLY] Reset Token for {email}:\n{reset_token}\n{'='*40}\n")
        
        if settings.smtp_user and settings.smtp_password:
            from email.message import EmailMessage
            import aiosmtplib
            
            message = EmailMessage()
            message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
            message["To"] = email
            message["Subject"] = "Reset Your Password"
            
            # The frontend URL for password reset, assuming Angular default port 4200
            # In a real app, this should come from a setting like settings.frontend_url
            reset_url = f"http://localhost:4200/auth/reset-password?token={reset_token}"
            
            message.set_content(f"""
            Hello {user.first_name},
            
            You requested a password reset. Please click the link below to set a new password:
            
            {reset_url}
            
            This link will expire in 30 minutes. If you did not request a password reset, please ignore this email.
            """)
            
            try:
                await aiosmtplib.send(
                    message,
                    hostname=settings.smtp_host,
                    port=settings.smtp_port,
                    start_tls=True,
                    username=settings.smtp_user,
                    password=settings.smtp_password,
                )
            except Exception as e:
                print(f"Failed to send reset email: {e}")
                
        return {"message": "If an account exists, a reset link has been sent to the email."}
        
    @staticmethod
    async def reset_password(db: AsyncSession, token: str, new_password: str) -> dict:
        """
        Verifies the reset token and updates the user's password.
        """
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            if payload.get("type") != "reset":
                raise BadRequestException(message="Invalid token type")
            user_id = payload.get("sub")
        except JWTError:
            raise BadRequestException(message="Reset link is invalid or expired")
            
        user = await user_repository.get_by_id(db, user_id)
        if not user:
            raise BadRequestException(message="User no longer exists")
            
        # Hash new password and save
        hashed_password = hash_password(new_password)
        
        # Also invalidate all current sessions by clearing refresh_token
        await user_repository.update(db, db_obj=user, obj_in={
            "password_hash": hashed_password,
            "refresh_token": None
        })
        
        from app.models.audit_log import AuditLog
        db.add(AuditLog(
            user_id=user.id,
            action="PASSWORD_RESET",
            resource_type="auth",
            resource_id=user.id,
            new_values={"details": "Password was reset successfully"}
        ))
        await db.commit()
        
        return {"message": "Password reset successfully. You can now log in."}


# Singleton instance
auth_service = AuthService()
