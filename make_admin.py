#!/usr/bin/env python3
import asyncio
import argparse
import sys
from sqlalchemy import select

# Setup python path so we can import from app
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.session import _get_session_factory
from app.models.user import User
from app.models.role import Role
from app.core.security import hash_password

async def make_admin(email: str, password: str = None):
    factory = _get_session_factory()
    async with factory() as db:
        # Get or create admin role
        role_query = select(Role).where(Role.name == "admin")
        result = await db.execute(role_query)
        admin_role = result.scalars().first()
        
        if not admin_role:
            print("Admin role does not exist. Creating it now...")
            admin_role = Role(name="admin", permissions={})
            db.add(admin_role)
            await db.commit()
            await db.refresh(admin_role)

        # Look for the user
        user_query = select(User).where(User.email == email)
        result = await db.execute(user_query)
        user = result.scalars().first()
        
        if user:
            # User exists, just update role (and password if provided)
            user.role_id = admin_role.id
            if password:
                user.password_hash = hash_password(password)
                print(f"Updated password for '{email}'.")
            await db.commit()
            print(f"SUCCESS: The user '{email}' is now an Admin!")
        else:
            # Create a brand new admin user
            if not password:
                print(f"ERROR: User '{email}' not found.")
                print("To create a brand new admin, you MUST provide a password using the --password flag.")
                sys.exit(1)
                
            print(f"User '{email}' not found. Creating new Admin user...")
            new_user = User(
                email=email,
                first_name="Super",
                last_name="Admin",
                password_hash=hash_password(password),
                role_id=admin_role.id,
                is_active=True,
                is_verified=True
            )
            db.add(new_user)
            await db.commit()
            print(f"SUCCESS: Created new Super Admin with email '{email}'!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Promote a user to Super Admin, or create a new one.")
    parser.add_argument("email", type=str, help="The email address of the admin.")
    parser.add_argument("--password", type=str, help="Password to set (required if creating a new user).", default=None)
    
    args = parser.parse_args()
    
    # Run async function
    asyncio.run(make_admin(args.email, args.password))
