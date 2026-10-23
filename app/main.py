from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session


from app.api.v1 import auth
from app.core.config import settings
from app.db.session import get_db

app = FastAPI(
        title=settings.app_name,
)

app.include_router(auth.router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/db-check")
def db_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"database": "connected"}