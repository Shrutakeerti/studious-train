from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.auth import create_access_token, get_current_user, hash_password, verify_password
from app.database import User, gen_id, get_db
from app.logging_config import get_logger
from app.schemas import LoginRequest, TokenOut, UserCreateRequest, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = get_logger(__name__)


@router.post("/signup", response_model=TokenOut, status_code=201)
def signup(payload: UserCreateRequest, db: DBSession = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    user = User(
        id=gen_id(),
        email=payload.email.lower(),
        name=payload.name,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=user.id)
    logger.info("New user signed up: %s", user.email)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut)
def login(payload: LoginRequest, db: DBSession = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(subject=user.id)
    logger.info("User logged in: %s", user.email)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user