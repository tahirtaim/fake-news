from fastapi import APIRouter, Form
from app.services.supabase_client import supabase

router = APIRouter()

@router.post("/signup")
def signup(email: str = Form(...), password: str = Form(...), name: str = Form(None), avatar: str = Form(None)):
    try:
        result = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "name": name,
                    "avatar_url": avatar
                }
            }
        })
        return {"message": "User created", "email": result.user.email}
    except Exception as e:
        return {"error": str(e)}

@router.post("/login")
def login(email: str = Form(...), password: str = Form(...)):
    try:
        result = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
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
