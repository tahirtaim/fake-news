from fastapi import APIRouter, Form, Header, File, UploadFile
from app.services.supabase_client import supabase
import time

router = APIRouter()

# ----------------- Update Profile -----------------
@router.post("/update-profile")
async def update_profile(
    name: str = Form(None),
    avatar: UploadFile = File(None),
    authorization: str = Header(...)
):
    """
    Update the profile of the currently logged-in user.
    Allows updating name and uploading avatar image to Supabase Storage.
    """
    try:
        # Extract token from Authorization header
        if not authorization.startswith("Bearer "):
            return {"error": "Invalid Authorization header format"}
        token = authorization.split(" ")[1]
        
        # Get current user using token
        user = supabase.auth.get_user(token).user
        
        # Prepare avatar upload (if provided)
        avatar_url = None
        if avatar and avatar.filename:
            # Read file content
            content = await avatar.read()
            file_ext = avatar.filename.split(".")[-1]
            timestamp = int(time.time())
            filename = f"{user.id}_{timestamp}.{file_ext}"
            
            # Upload to Supabase Storage bucket "avatars"
            response = supabase.storage.from_("avatars").upload(
                path=filename,
                file=content,
                file_options={
                    "content-type": avatar.content_type,
                    "upsert": "true"
                }
            )
            print("Avatar uploaded:", response)
            
            # Get public URL
            avatar_url = supabase.storage.from_("avatars").get_public_url(filename)
        
        # Prepare update data
        user_data = {}
        if name:
            user_data["name"] = name
        if avatar_url:
            user_data["avatar_url"] = avatar_url
            
        # Update user metadata in Supabase
        supabase.auth.update_user({
            "data": user_data
        })
        
        # Get updated user info
        updated_user = supabase.auth.get_user(token).user
        
        return {
            "message": "Profile updated successfully",
            "email": updated_user.email,
            "name": updated_user.user_metadata.get("name") if hasattr(updated_user, "user_metadata") else None,
            "avatar_url": updated_user.user_metadata.get("avatar_url") if hasattr(updated_user, "user_metadata") else None
        }

    except Exception as e:
        return {"error": str(e)}


# ----------------- Get Profile -----------------
@router.get("/get-profile")
async def get_profile(authorization: str = Header(...)):
    """
    Retrieve the profile information of the currently authenticated user.
    Requires Bearer token in Authorization header.
    """
    try:
        # Validate token format
        if not authorization.startswith("Bearer "):
            return {"error": "Invalid Authorization header format"}
        token = authorization.split(" ")[1]

        # Get user from Supabase
        user = supabase.auth.get_user(token).user

        if not user:
            return {"error": "User not found or invalid token"}

        # Prepare and return user data
        user_data = {
            "email": user.email,
            "id": user.id,
            "name": user.user_metadata.get("name") if hasattr(user, "user_metadata") else None,
            "avatar_url": user.user_metadata.get("avatar_url") if hasattr(user, "user_metadata") else None,
            "created_at": getattr(user, "created_at", None)
        }

        return {
            "message": "Profile fetched successfully",
            "user": user_data
        }

    except Exception as e:
        return {"error": str(e)}

