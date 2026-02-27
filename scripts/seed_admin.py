"""
Seed script — Create or promote a user to admin.
Usage:
  python scripts/seed_admin.py                    # Interactive
  python scripts/seed_admin.py user@email.com     # Promote existing user
"""
import os
import sys
from pathlib import Path

# Setup paths
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "backend"))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from app.database import SessionLocal, init_db
from app.models.user import User, Subscription, PlanType, SubscriptionStatus
from app.auth import hash_password
from datetime import datetime, timedelta


def main():
    db = SessionLocal()
    init_db()

    email = sys.argv[1] if len(sys.argv) > 1 else None

    if not email:
        print("=== Seed Admin ===")
        print("1. Promote existing user to admin")
        print("2. Create new admin user")
        choice = input("Choose (1/2): ").strip()

        if choice == "1":
            email = input("Email: ").strip().lower()
            user = db.query(User).filter(User.email == email).first()
            if not user:
                print(f"User '{email}' not found!")
                db.close()
                return
            user.is_admin = True
            # Also ensure Pro subscription
            sub = user.subscription
            if sub:
                sub.plan = PlanType.PRO
                sub.status = SubscriptionStatus.ACTIVE
                sub.subscribed_at = datetime.utcnow()
                sub.expires_at = datetime.utcnow() + timedelta(days=365 * 10)
                sub.payment_ref = "admin_seed"
            else:
                sub = Subscription(
                    user_id=user.id,
                    plan=PlanType.PRO,
                    status=SubscriptionStatus.ACTIVE,
                    subscribed_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(days=365 * 10),
                    payment_ref="admin_seed",
                )
                db.add(sub)
            db.commit()
            print(f"User '{email}' promoted to admin with Pro subscription!")
        elif choice == "2":
            email = input("Email: ").strip().lower()
            name = input("Name: ").strip()
            password = input("Password: ").strip()

            # Check if exists
            existing = db.query(User).filter(User.email == email).first()
            if existing:
                existing.is_admin = True
                db.commit()
                print(f"User '{email}' already exists — promoted to admin!")
            else:
                user = User(
                    email=email,
                    name=name,
                    password_hash=hash_password(password),
                    is_admin=True,
                )
                db.add(user)
                db.flush()

                # Create Pro subscription (admin = unlimited)
                sub = Subscription(
                    user_id=user.id,
                    plan=PlanType.PRO,
                    status=SubscriptionStatus.ACTIVE,
                    subscribed_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(days=365 * 10),
                    payment_ref="admin_seed",
                )
                db.add(sub)
                db.commit()
                print(f"Admin '{email}' created with Pro subscription!")
        else:
            print("Invalid choice.")
    else:
        # Promote existing user by email (CLI arg)
        email = email.lower().strip()
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"User '{email}' not found!")
        else:
            user.is_admin = True
            db.commit()
            print(f"User '{email}' promoted to admin!")

    db.close()


if __name__ == "__main__":
    main()
