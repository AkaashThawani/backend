"""
Initialize the database with all tables
"""
from app.models import init_db

if __name__ == "__main__":
    print("Creating database tables...")
    init_db()
    print("✅ Database tables created successfully!")
    print("\nNow run: python seed_data.py")
