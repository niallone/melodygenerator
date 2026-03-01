import jwt
from fastapi import Depends, HTTPException, Request, WebSocket
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.src.config import Settings

security = HTTPBearer()

_settings = None

# In-memory token blacklist (for token revocation)
_revoked_tokens: set[str] = set()


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def get_db(request: Request):
    """Get database instance from app state."""
    return request.app.state.pg_db


def get_models(request: Request):
    """Get loaded models from app state."""
    return request.app.state.models


def revoke_token(jti: str):
    """Add a token's JTI to the revocation blacklist."""
    _revoked_tokens.add(jti)


def is_token_revoked(jti: str) -> bool:
    """Check if a token has been revoked."""
    return jti in _revoked_tokens


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Validate JWT token and return current user."""
    settings = get_settings()
    db = request.app.state.pg_db
    token = credentials.credentials

    try:
        data = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        # Check if token has been revoked
        jti = data.get("jti")
        if jti and is_token_revoked(jti):
            raise HTTPException(status_code=401, detail="Token has been revoked")
        current_user = await db.fetchrow("SELECT * FROM admin_users WHERE id = $1", data["user_id"])
        if current_user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return current_user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Something went wrong")


async def get_current_admin(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Validate JWT token and ensure user has admin role."""
    user = await get_current_user(request, credentials)
    role = user.get("role") if hasattr(user, "get") else getattr(user, "role", None)
    if role != "admin" and role != 1:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


async def validate_websocket_token(websocket: WebSocket) -> dict | None:
    """Validate JWT token from WebSocket query params. Returns decoded token data or None."""
    token = websocket.query_params.get("token")
    if not token:
        return None

    settings = get_settings()
    try:
        data = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        jti = data.get("jti")
        if jti and is_token_revoked(jti):
            return None
        return data
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
