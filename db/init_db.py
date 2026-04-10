"""
Utility script to initialize the database.
Run this script to create all tables.
"""

from database import create_db_and_tables

if __name__ == "__main__":
    print("Creating database and tables...")
    create_db_and_tables()
    print("Database initialized successfully!")
