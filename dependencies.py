from app_data import database



def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()
