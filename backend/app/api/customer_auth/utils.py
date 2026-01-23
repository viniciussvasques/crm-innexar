"""Customer Authentication Utilities"""
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from fastapi import HTTPException

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TOKEN_EXPIRE_DAYS = 7
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(customer_id: int, email: str) -> str:
    payload = {
        "sub": str(customer_id),
        "email": email,
        "type": "customer",
        "exp": datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "customer":
            raise HTTPException(status_code=401, detail="Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_token_from_request(authorization: str = None, token_param: str = None) -> str:
    if authorization and authorization.startswith("Bearer "):
        return authorization.replace("Bearer ", "")
    if token_param:
        return token_param
    raise HTTPException(status_code=401, detail="Token required")
