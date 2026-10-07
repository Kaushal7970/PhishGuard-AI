import json
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Scan, User
from app.schemas import Credentials, PredictionRequest, PredictionResponse, RegisterRequest, ScanResponse, TokenResponse, UserResponse
from app.security import create_access_token, get_current_user, hash_password, require_admin, verify_password
from app.services.predictor import predictor

router = APIRouter(prefix="/api")


@router.get("/health")
def health():
    return {"status": "ok", "service": "phishguard-ai"}


@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email is already registered")
    user = User(name=payload.name, email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: Credentials, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenResponse(access_token=create_access_token(user))


@router.post("/predict", response_model=PredictionResponse)
def predict(payload: PredictionRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = predictor.predict(str(payload.url))
    scan = Scan(user_id=user.id, url=result["url"], prediction=result["prediction"], probability=result["probability"], risk_score=result["risk_score"], risk_level=result["risk_level"], indicators=json.dumps(result["indicators"]))
    db.add(scan)
    db.commit()
    db.refresh(scan)
    result["id"] = scan.id
    result["created_at"] = scan.created_at
    return result


@router.get("/history", response_model=list[ScanResponse])
def history(limit: int = Query(50, ge=1, le=200), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    scans = db.query(Scan).filter(Scan.user_id == user.id).order_by(desc(Scan.created_at)).limit(limit).all()
    return [{**scan.__dict__, "indicators": json.loads(scan.indicators)} for scan in scans]


@router.get("/analytics")
def analytics(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(Scan.prediction, func.count(Scan.id)).filter(Scan.user_id == user.id).group_by(Scan.prediction).all()
    counts = Counter({prediction: count for prediction, count in rows})
    total = sum(counts.values())
    return {"total_scans": total, "legitimate": counts["LEGITIMATE"], "suspicious": counts["SUSPICIOUS"], "phishing": counts["PHISHING"], "detection_percentage": round(counts["PHISHING"] / total * 100, 2) if total else 0}


@router.get("/admin/users", response_model=list[UserResponse])
def admin_users(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id).all()


@router.get("/admin/scans", response_model=list[ScanResponse])
def admin_scans(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    scans = db.query(Scan).order_by(desc(Scan.created_at)).limit(500).all()
    return [{**scan.__dict__, "indicators": json.loads(scan.indicators)} for scan in scans]


@router.delete("/admin/scans/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scan(scan_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    db.delete(scan)
    db.commit()
