from fastapi import APIRouter
from pydantic import BaseModel
from app.services.supabase_client import supabase

router = APIRouter()

# ----------------- Pydantic Models -----------------
class SignupRequest(BaseModel):
    email: str
    password: str
    name: str = None
    avatar: str = None

class LoginRequest(BaseModel):
    email: str
    password: str

# ----------------- Signup -----------------
@router.post("/signup")
def signup(request: SignupRequest):
    try:
        result = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {
                    "name": request.name,
                    "avatar_url": request.avatar
                }
            }
        })

        return {
            "message": "User created",
            "email": result.user.email,
            "access_token": result.session.access_token if result.session else None,
            "avatar_url": result.user.user_metadata.get("avatar_url")
        }
    except Exception as e:
        return {"error": str(e)}

# ----------------- Login -----------------
@router.post("/login")
def login(request: LoginRequest):
    try:
        result = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })

        if result.session:
            return {
                "message": "Login successful",
                "email": result.user.email,
                "name": result.user.user_metadata.get("name"),
                "avatar_url": result.user.user_metadata.get("avatar_url"),
                "access_token": result.session.access_token
            }
        else:
            return {"error": "Invalid credentials"}

    except Exception as e:
        return {"error": str(e)}
