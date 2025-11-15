import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.utils.security import get_password_hash


def create_admin_user():
    db = SessionLocal()
    
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.username == "admin").first()
        
        if admin:
            print("✅ Admin user already exists")
            print(f"Username: {admin.username}")
            print(f"Email: {admin.email}")
            return
        
        # Create admin user with simple password
        admin_password = "admin123"
        
        print("Creating admin user...")
        print(f"Hashing password: {admin_password}")
        
        hashed_password = get_password_hash(admin_password)
        print(f"Password hashed successfully")
        
        admin = User(
            email="admin@docuflow.ai",
            username="admin",
            full_name="System Administrator",
            hashed_password=hashed_password,
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print("\n✅ Admin user created successfully!")
        print("=" * 50)
        print(f"Username: admin")
        print(f"Password: admin123")
        print(f"Email: admin@docuflow.ai")
        print(f"Role: {admin.role}")
        print("=" * 50)
        print("⚠️  Please change the password after first login!")
        print("\nYou can now login at: http://localhost:3000/login")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("DocuFlow AI - Admin User Setup")
    print("=" * 50)
    create_admin_user()