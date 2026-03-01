from datetime import datetime
from typing import Optional

import bcrypt
from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, EmailStr, Field

from app.src.dependencies import get_current_user
from app.src.errors.api import APIError

router = APIRouter()


# --- Pydantic request models ---


class CreateAccountUserRequest(BaseModel):
    account_id: int
    password: str = Field(min_length=8)
    role: int


class UpdateAccountUserRequest(BaseModel):
    account_id: Optional[int] = None
    password: Optional[str] = Field(default=None, min_length=8)
    role: Optional[int] = None


class CreateAccountUserRoleRequest(BaseModel):
    slug: str
    name: str


class UpdateAccountUserRoleRequest(BaseModel):
    slug: Optional[str] = None
    name: Optional[str] = None


class CreateAccountRequest(BaseModel):
    first_name: str
    last_name: str
    business_name: Optional[str] = None
    business_abn: Optional[int] = None
    phone: Optional[str] = None
    email: EmailStr
    account_address_id: Optional[int] = None


class UpdateAccountRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    business_name: Optional[str] = None
    business_abn: Optional[int] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    account_address_id: Optional[int] = None


class CreateAccountAddressRequest(BaseModel):
    unit: Optional[str] = None
    street: str
    suburb_city: str
    postcode: int
    state_id: int


class UpdateAccountAddressRequest(BaseModel):
    unit: Optional[str] = None
    street: Optional[str] = None
    suburb_city: Optional[str] = None
    postcode: Optional[int] = None
    state_id: Optional[int] = None


class CreateAUStateRequest(BaseModel):
    name: str
    country_id: int


class UpdateAUStateRequest(BaseModel):
    name: Optional[str] = None
    country_id: Optional[int] = None


class CreateCountryRequest(BaseModel):
    name: str
    active: Optional[bool] = True


class UpdateCountryRequest(BaseModel):
    name: Optional[str] = None
    active: Optional[bool] = None


# --- Helpers ---


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _parse_delete_count(result: str) -> int:
    """Parse the row count from a DELETE command tag like 'DELETE 1'."""
    try:
        return int(result.split()[-1])
    except (ValueError, IndexError):
        return 0


# --- Account User CRUD ---


@router.post("/account_user", status_code=201)
async def create_account_user(body: CreateAccountUserRequest, request: Request, current_user=Depends(get_current_user)):
    try:
        password_hash = hash_password(body.password)
        query = """
        INSERT INTO account_user (account_id, password_hash, role)
        VALUES ($1, $2, $3)
        RETURNING id
        """
        db = request.app.state.pg_db
        user_id = await db.fetchval(query, body.account_id, password_hash, body.role)
        return {"message": "Account user created successfully", "id": user_id}
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Error creating account user: {str(e)}", status_code=500)


@router.get("/account_user")
async def get_all_account_users(
    request: Request,
    current_user=Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    try:
        db = request.app.state.pg_db
        users = await db.fetch("SELECT * FROM account_user LIMIT $1 OFFSET $2", limit, offset)
        return [dict(row) for row in users]
    except Exception as e:
        raise APIError(f"Error fetching account users: {str(e)}", status_code=500)


@router.get("/account_user/{user_id}")
async def get_account_user(user_id: int, request: Request, current_user=Depends(get_current_user)):
    try:
        db = request.app.state.pg_db
        user = await db.fetchrow("SELECT * FROM account_user WHERE id = $1", user_id)
        if user is None:
            raise APIError("Account user not found", status_code=404)
        return dict(user)
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Error fetching account user: {str(e)}", status_code=500)


@router.put("/account_user/{user_id}")
async def update_account_user(
    user_id: int, body: UpdateAccountUserRequest, request: Request, current_user=Depends(get_current_user)
):
    try:
        db = request.app.state.pg_db
        password_hash = hash_password(body.password) if body.password else None
        query = """
        UPDATE account_user
        SET account_id = COALESCE($1, account_id),
            password_hash = COALESCE($2, password_hash),
            role = COALESCE($3, role),
            modified = $4
        WHERE id = $5
        """
        await db.execute(query, body.account_id, password_hash, body.role, datetime.now(), user_id)
        return {"message": "Account user updated successfully"}
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Error updating account user: {str(e)}", status_code=500)


@router.delete("/account_user/{user_id}")
async def delete_account_user(user_id: int, request: Request, current_user=Depends(get_current_user)):
    try:
        db = request.app.state.pg_db
        result = await db.execute("DELETE FROM account_user WHERE id = $1", user_id)
        if _parse_delete_count(result) >= 1:
            return {"message": "Account user deleted successfully"}
        else:
            raise APIError("Account user not found", status_code=404)
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Error deleting account user: {str(e)}", status_code=500)


# --- Account User Role CRUD ---


@router.post("/account_user_role", status_code=201)
async def create_account_user_role(
    body: CreateAccountUserRoleRequest, request: Request, current_user=Depends(get_current_user)
):
    try:
        query = """
        INSERT INTO account_user_role (slug, name)
        VALUES ($1, $2)
        RETURNING id
        """
        db = request.app.state.pg_db
        role_id = await db.fetchval(query, body.slug, body.name)
        return {"message": "Account user role created successfully", "id": role_id}
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Error creating account user role: {str(e)}", status_code=500)


@router.get("/account_user_role")
async def get_all_account_user_roles(
    request: Request,
    current_user=Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    try:
        db = request.app.state.pg_db
        roles = await db.fetch("SELECT * FROM account_user_role LIMIT $1 OFFSET $2", limit, offset)
        return [dict(row) for row in roles]
    except Exception as e:
        raise APIError(f"Error fetching account user roles: {str(e)}", status_code=500)


@router.get("/account_user_role/{role_id}")
async def get_account_user_role(role_id: int, request: Request, current_user=Depends(get_current_user)):
    try:
        db = request.app.state.pg_db
        role = await db.fetchrow("SELECT * FROM account_user_role WHERE id = $1", role_id)
        if role is None:
            raise APIError("Account user role not found", status_code=404)
        return dict(role)
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Error fetching account user role: {str(e)}", status_code=500)


@router.put("/account_user_role/{role_id}")
async def update_account_user_role(
    role_id: int, body: UpdateAccountUserRoleRequest, request: Request, current_user=Depends(get_current_user)
):
    try:
        db = request.app.state.pg_db
        query = """
        UPDATE account_user_role
        SET slug = COALESCE($1, slug),
            name = COALESCE($2, name),
            modified = $3
        WHERE id = $4
        """
        await db.execute(query, body.slug, body.name, datetime.now(), role_id)
        return {"message": "Account user role updated successfully"}
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Error updating account user role: {str(e)}", status_code=500)


@router.delete("/account_user_role/{role_id}")
async def delete_account_user_role(role_id: int, request: Request, current_user=Depends(get_current_user)):
    try:
        db = request.app.state.pg_db
        result = await db.execute("DELETE FROM account_user_role WHERE id = $1", role_id)
        if _parse_delete_count(result) >= 1:
            return {"message": "Account user role deleted successfully"}
        else:
            raise APIError("Account user role not found", status_code=404)
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Error deleting account user role: {str(e)}", status_code=500)


# --- Account CRUD ---


@router.post("/account", status_code=201)
async def create_account(body: CreateAccountRequest, request: Request, current_user=Depends(get_current_user)):
    try:
        query = """
        INSERT INTO account (first_name, last_name, business_name, business_abn, phone, email, account_address_id)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id
        """
        db = request.app.state.pg_db
        account_id = await db.fetchval(
            query,
            body.first_name,
            body.last_name,
            body.business_name,
            body.business_abn,
            body.phone,
            body.email,
            body.account_address_id,
        )
        return {"message": "Account created successfully", "id": account_id}
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Error creating account: {str(e)}", status_code=500)


@router.get("/account")
async def get_all_accounts(
    request: Request,
    current_user=Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    try:
        db = request.app.state.pg_db
        accounts = await db.fetch("SELECT * FROM account LIMIT $1 OFFSET $2", limit, offset)
        return [dict(row) for row in accounts]
    except Exception as e:
        raise APIError(f"Error fetching accounts: {str(e)}", status_code=500)


@router.get("/account/{account_id}")
async def get_account(account_id: int, request: Request, current_user=Depends(get_current_user)):
    try:
        db = request.app.state.pg_db
        account = await db.fetchrow("SELECT * FROM account WHERE id = $1", account_id)
        if account is None:
            raise APIError("Account not found", status_code=404)
        return dict(account)
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Error fetching account: {str(e)}", status_code=500)


@router.put("/account/{account_id}")
async def update_account(
    account_id: int, body: UpdateAccountRequest, request: Request, current_user=Depends(get_current_user)
):
    try:
        db = request.app.state.pg_db
        query = """
        UPDATE account
        SET first_name = COALESCE($1, first_name),
            last_name = COALESCE($2, last_name),
            business_name = $3,
            business_abn = $4,
            phone = COALESCE($5, phone),
            email = COALESCE($6, email),
            account_address_id = $7
        WHERE id = $8
        """
        await db.execute(
            query,
            body.first_name,
            body.last_name,
            body.business_name,
            body.business_abn,
            body.phone,
            body.email,
            body.account_address_id,
            account_id,
        )
        return {"message": "Account updated successfully"}
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Error updating account: {str(e)}", status_code=500)


@router.delete("/account/{account_id}")
async def delete_account(account_id: int, request: Request, current_user=Depends(get_current_user)):
    try:
        db = request.app.state.pg_db
        result = await db.execute("DELETE FROM account WHERE id = $1", account_id)
        if _parse_delete_count(result) >= 1:
            return {"message": "Account deleted successfully"}
        else:
            raise APIError("Account not found", status_code=404)
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Error deleting account: {str(e)}", status_code=500)


# --- Account Address CRUD ---


@router.post("/account_address", status_code=201)
async def create_account_address(
    body: CreateAccountAddressRequest, request: Request, current_user=Depends(get_current_user)
):
    try:
        query = """
        INSERT INTO account_address (unit, street, suburb_city, postcode, state_id)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
        """
        db = request.app.state.pg_db
        address_id = await db.fetchval(query, body.unit, body.street, body.suburb_city, body.postcode, body.state_id)
        return {"message": "Account address created successfully", "id": address_id}
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Error creating account address: {str(e)}", status_code=500)


@router.get("/account_address")
async def get_all_account_addresses(
    request: Request,
    current_user=Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    try:
        db = request.app.state.pg_db
        addresses = await db.fetch("SELECT * FROM account_address LIMIT $1 OFFSET $2", limit, offset)
        return [dict(row) for row in addresses]
    except Exception as e:
        raise APIError(f"Error fetching account addresses: {str(e)}", status_code=500)


@router.get("/account_address/{address_id}")
async def get_account_address(address_id: int, request: Request, current_user=Depends(get_current_user)):
    try:
        db = request.app.state.pg_db
        address = await db.fetchrow("SELECT * FROM account_address WHERE id = $1", address_id)
        if address is None:
            raise APIError("Account address not found", status_code=404)
        return dict(address)
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Error fetching account address: {str(e)}", status_code=500)


@router.put("/account_address/{address_id}")
async def update_account_address(
    address_id: int, body: UpdateAccountAddressRequest, request: Request, current_user=Depends(get_current_user)
):
    try:
        db = request.app.state.pg_db
        query = """
        UPDATE account_address
        SET unit = COALESCE($1, unit),
            street = COALESCE($2, street),
            suburb_city = COALESCE($3, suburb_city),
            postcode = COALESCE($4, postcode),
            state_id = COALESCE($5, state_id),
            modified = $6
        WHERE id = $7
        """
        await db.execute(
            query, body.unit, body.street, body.suburb_city, body.postcode, body.state_id, datetime.now(), address_id
        )
        return {"message": "Account address updated successfully"}
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Error updating account address: {str(e)}", status_code=500)


@router.delete("/account_address/{address_id}")
async def delete_account_address(address_id: int, request: Request, current_user=Depends(get_current_user)):
    try:
        db = request.app.state.pg_db
        result = await db.execute("DELETE FROM account_address WHERE id = $1", address_id)
        if _parse_delete_count(result) >= 1:
            return {"message": "Account address deleted successfully"}
        else:
            raise APIError("Account address not found", status_code=404)
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Error deleting account address: {str(e)}", status_code=500)


# --- Account Address AU State CRUD ---


@router.post("/account_address_au_state", status_code=201)
async def create_account_address_au_state(
    body: CreateAUStateRequest, request: Request, current_user=Depends(get_current_user)
):
    try:
        query = """
        INSERT INTO account_address_au_state (name, country_id)
        VALUES ($1, $2)
        RETURNING id
        """
        db = request.app.state.pg_db
        state_id = await db.fetchval(query, body.name, body.country_id)
        return {"message": "Account address AU state created successfully", "id": state_id}
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Error creating account address AU state: {str(e)}", status_code=500)


@router.get("/account_address_au_state")
async def get_all_account_address_au_states(
    request: Request,
    current_user=Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    try:
        db = request.app.state.pg_db
        states = await db.fetch("SELECT * FROM account_address_au_state LIMIT $1 OFFSET $2", limit, offset)
        return [dict(row) for row in states]
    except Exception as e:
        raise APIError(f"Error fetching account address AU states: {str(e)}", status_code=500)


@router.get("/account_address_au_state/{state_id}")
async def get_account_address_au_state(state_id: int, request: Request, current_user=Depends(get_current_user)):
    try:
        db = request.app.state.pg_db
        state = await db.fetchrow("SELECT * FROM account_address_au_state WHERE id = $1", state_id)
        if state is None:
            raise APIError("Account address AU state not found", status_code=404)
        return dict(state)
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Error fetching account address AU state: {str(e)}", status_code=500)


@router.put("/account_address_au_state/{state_id}")
async def update_account_address_au_state(
    state_id: int, body: UpdateAUStateRequest, request: Request, current_user=Depends(get_current_user)
):
    try:
        db = request.app.state.pg_db
        query = """
        UPDATE account_address_au_state
        SET name = COALESCE($1, name),
            country_id = COALESCE($2, country_id),
            modified = $3
        WHERE id = $4
        """
        await db.execute(query, body.name, body.country_id, datetime.now(), state_id)
        return {"message": "Account address AU state updated successfully"}
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Error updating account address AU state: {str(e)}", status_code=500)


@router.delete("/account_address_au_state/{state_id}")
async def delete_account_address_au_state(state_id: int, request: Request, current_user=Depends(get_current_user)):
    try:
        db = request.app.state.pg_db
        result = await db.execute("DELETE FROM account_address_au_state WHERE id = $1", state_id)
        if _parse_delete_count(result) >= 1:
            return {"message": "Account address AU state deleted successfully"}
        else:
            raise APIError("Account address AU state not found", status_code=404)
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Error deleting account address AU state: {str(e)}", status_code=500)


# --- Account Address Country CRUD ---


@router.post("/account_address_country", status_code=201)
async def create_account_address_country(
    body: CreateCountryRequest, request: Request, current_user=Depends(get_current_user)
):
    try:
        query = """
        INSERT INTO account_address_country (name, active)
        VALUES ($1, $2)
        RETURNING id
        """
        db = request.app.state.pg_db
        country_id = await db.fetchval(query, body.name, body.active)
        return {"message": "Account address country created successfully", "id": country_id}
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Error creating account address country: {str(e)}", status_code=500)


@router.get("/account_address_country")
async def get_all_account_address_countries(
    request: Request,
    current_user=Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    try:
        db = request.app.state.pg_db
        query = """
        SELECT * FROM account_address_country
        ORDER BY active DESC, name ASC
        LIMIT $1 OFFSET $2
        """
        countries = await db.fetch(query, limit, offset)
        return [dict(row) for row in countries]
    except Exception as e:
        raise APIError(f"Error fetching account address countries: {str(e)}", status_code=500)


@router.get("/account_address_country/{country_id}")
async def get_account_address_country(country_id: int, request: Request, current_user=Depends(get_current_user)):
    try:
        db = request.app.state.pg_db
        country = await db.fetchrow("SELECT * FROM account_address_country WHERE id = $1", country_id)
        if country is None:
            raise APIError("Account address country not found", status_code=404)
        return dict(country)
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Error fetching account address country: {str(e)}", status_code=500)


@router.put("/account_address_country/{country_id}")
async def update_account_address_country(
    country_id: int, body: UpdateCountryRequest, request: Request, current_user=Depends(get_current_user)
):
    try:
        db = request.app.state.pg_db
        query = """
        UPDATE account_address_country
        SET name = COALESCE($1, name),
            active = COALESCE($2, active),
            modified = $3
        WHERE id = $4
        """
        await db.execute(query, body.name, body.active, datetime.now(), country_id)
        return {"message": "Account address country updated successfully"}
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Error updating account address country: {str(e)}", status_code=500)


@router.delete("/account_address_country/{country_id}")
async def delete_account_address_country(country_id: int, request: Request, current_user=Depends(get_current_user)):
    try:
        db = request.app.state.pg_db
        result = await db.execute("DELETE FROM account_address_country WHERE id = $1", country_id)
        if _parse_delete_count(result) >= 1:
            return {"message": "Account address country deleted successfully"}
        else:
            raise APIError("Account address country not found", status_code=404)
    except APIError:
        raise
    except Exception as e:
        raise APIError(f"Error deleting account address country: {str(e)}", status_code=500)
