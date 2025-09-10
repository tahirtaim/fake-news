from fastapi import APIRouter, Form, Header
from app.services.supabase_client import supabase

router = APIRouter()

@router.post("/update-profile")
def update_profile(name: str = Form(None), avatar_url: str = Form(None), authorization: str = Header(...)):
    try:
        token = authorization.split(" ")[1]  # Bearer <token>
        user = supabase.auth.get_user(token).user

        updated_user = supabase.auth.update_user({
            "data": {
                "name": name,
                "avatar_url": avatar_url
            }
        })

        return {
            "message": "Profile updated",
            "email": updated_user.user.email,
            "name": updated_user.user.user_metadata.get("name"),
            "avatar_url": updated_user.user.user_metadata.get("avatar_url")
        }

    except Exception as e:
        return {"error": str(e)}
