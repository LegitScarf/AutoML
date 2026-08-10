import os
import sys
from sqlalchemy import create_engine, text

# Add parent directory to path to resolve backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from backend.db.database import DATABASE_URL

print(f"Connecting to database: {DATABASE_URL}")
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE runs ADD COLUMN plan TEXT;"))
        conn.commit()
    print("Migration successful: Added 'plan' column to 'runs' table.")
except Exception as e:
    print(f"Migration completed with message: {str(e)}")
