import os

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database import get_db, engine
from models import Base, URL
from schemas import URLRequest
from utils import generate_short_code

app = FastAPI()

# Base URL (Render or local fallback)
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")

# Create tables on startup
Base.metadata.create_all(bind=engine)


# ---------------------------
# Helper: Unique code generator
# ---------------------------
def get_unique_code(db: Session):
    while True:
        code = generate_short_code()
        exists = db.query(URL).filter(URL.short_code == code).first()
        if not exists:
            return code


# ---------------------------
# 1. Shorten URL
# ---------------------------
@app.post("/shorten")
def shorten_url(request: URLRequest, db: Session = Depends(get_db)):
    short_code = get_unique_code(db)

    new_url = URL(
        original_url=request.original_url,
        short_code=short_code
    )

    db.add(new_url)
    db.commit()
    db.refresh(new_url)

    return {
        "original_url": new_url.original_url,
        "short_code": short_code,
        "short_url": f"{BASE_URL}/{short_code}"
    }


# ---------------------------
# 2. Redirect to original URL
# ---------------------------
@app.get("/{short_code}")
def redirect_url(short_code: str, db: Session = Depends(get_db)):
    # normalize input (VERY IMPORTANT)
    short_code = short_code.strip()

    # fetch from DB
    url = db.query(URL).filter(URL.short_code == short_code).first()

    if not url:
        raise HTTPException(status_code=404, detail="URL not found")

    # safe increment
    url.click_count = (url.click_count or 0) + 1
    db.commit()

    # proper redirect
    return RedirectResponse(url=url.original_url, status_code=307)


# ---------------------------
# 3. Analytics
# ---------------------------
@app.get("/analytics/{short_code}")
def analytics(short_code: str, db: Session = Depends(get_db)):
    url = db.query(URL).filter(URL.short_code == short_code).first()

    if not url:
        raise HTTPException(status_code=404, detail="URL not found")

    return {
        "original_url": url.original_url,
        "short_code": url.short_code,
        "clicks": url.click_count
    }