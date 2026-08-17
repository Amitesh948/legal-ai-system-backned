"""
Fix PostgreSQL enum types: rename UPPERCASE values to lowercase.
Uses SYNC connection (same as alembic) which is proven to work.
"""
from sqlalchemy import create_engine, text
from app.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url_sync)

with engine.connect() as conn:
    print("Fixing case_priority_enum...")
    conn.execute(text("ALTER TYPE case_priority_enum RENAME VALUE 'LOW' TO 'low'"))
    conn.execute(text("ALTER TYPE case_priority_enum RENAME VALUE 'MEDIUM' TO 'medium'"))
    conn.execute(text("ALTER TYPE case_priority_enum RENAME VALUE 'HIGH' TO 'high'"))
    conn.execute(text("ALTER TYPE case_priority_enum RENAME VALUE 'URGENT' TO 'urgent'"))

    print("Fixing case_status_enum...")
    conn.execute(text("ALTER TYPE case_status_enum RENAME VALUE 'NEW' TO 'new'"))
    conn.execute(text("ALTER TYPE case_status_enum RENAME VALUE 'PAYMENT_PENDING' TO 'payment_pending'"))
    conn.execute(text("ALTER TYPE case_status_enum RENAME VALUE 'PAYMENT_COMPLETED' TO 'payment_completed'"))
    conn.execute(text("ALTER TYPE case_status_enum RENAME VALUE 'PAYMENT_FAILED' TO 'payment_failed'"))
    conn.execute(text("ALTER TYPE case_status_enum RENAME VALUE 'DOCUMENTS_UPLOADED' TO 'documents_uploaded'"))
    conn.execute(text("ALTER TYPE case_status_enum RENAME VALUE 'AI_PROCESSING' TO 'ai_processing'"))
    conn.execute(text("ALTER TYPE case_status_enum RENAME VALUE 'UNDER_REVIEW' TO 'under_review'"))
    conn.execute(text("ALTER TYPE case_status_enum RENAME VALUE 'OPINION_GENERATED' TO 'opinion_generated'"))
    conn.execute(text("ALTER TYPE case_status_enum RENAME VALUE 'REPORT_GENERATED' TO 'report_generated'"))
    conn.execute(text("ALTER TYPE case_status_enum RENAME VALUE 'COMPLETED' TO 'completed'"))
    conn.execute(text("ALTER TYPE case_status_enum RENAME VALUE 'CANCELLED' TO 'cancelled'"))

    conn.commit()
    print("SUCCESS: All enum values fixed to lowercase!")
