import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import APIRouter, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.src.dependencies import revoke_token
from app.src.errors.api import APIError

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
@limiter.limit("5/minute")
async def login(body: LoginRequest, request: Request):
    db = request.app.state.pg_db
    settings = request.app.state.settings

    if not body.email or not body.password:
        raise APIError("Missing email or password", status_code=400)

    query = """
    SELECT au.id, au.password_hash, a.email
    FROM account_user au
    JOIN account a ON au.account_id = a.id
    WHERE a.email = $1
    """

    user = await db.fetchrow(query, body.email)

    if not user:
        raise APIError("Invalid email or password", status_code=401)

    if not bcrypt.checkpw(body.password.encode("utf-8"), user["password_hash"].encode("utf-8")):
        raise APIError("Invalid email or password", status_code=401)

    jti = str(uuid.uuid4())
    token = jwt.encode(
        {
            "user_id": user["id"],
            "jti": jti,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc),
        },
        settings.secret_key,
        algorithm="HS256",
    )

    return {"token": token}


@router.post("/logout")
async def logout(request: Request):
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        settings = request.app.state.settings
        try:
            data = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
            jti = data.get("jti")
            if jti:
                revoke_token(jti)
        except jwt.InvalidTokenError:
            pass
    return {"message": "Successfully logged out"}
