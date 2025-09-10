from fastapi import APIRouter, Form, Header, File, UploadFile
from app.services.supabase_client import supabase
import time

router = APIRouter()

@router.post("/update-profile")
async def update_profile(
    name: str = Form(None),
    avatar: UploadFile = File(None),
    authorization: str = Header(...)
):
    try:
        # Extract token
        token = authorization.split(" ")[1]  # Bearer <token>
        
        # Get current user 
        user = supabase.auth.get_user(token).user
        
        # Process avatar upload if provided
        avatar_url = None
        if avatar and avatar.filename:
            # Read file content
            content = await avatar.read()
            # Generate a unique filename
            file_ext = avatar.filename.split(".")[-1]
            timestamp = int(time.time())
            filename = f"{user.id}_{timestamp}.{file_ext}"
            
            # Upload to Supabase Storage using the format from docs
            response = supabase.storage.from_("avatars").upload(
                path=filename,
                file=content,
                file_options={
                    "content-type": avatar.content_type,
                    "upsert": "true"
                }
            )
            print(response)
            # Get public URL
            avatar_url = supabase.storage.from_("avatars").get_public_url(filename)
        
        # Prepare user data for update
        user_data = {}
        if name:
            user_data["name"] = name
        if avatar_url:
            user_data["avatar_url"] = avatar_url
            
        # Update user data
        supabase.auth.update_user({
            "data": user_data
        })
        # Get the updated user info
        updated_user = supabase.auth.get_user(token).user
        
        return {
            "message": "Profile updated",
            "email": updated_user.email,
            "name": updated_user.user_metadata.get("name") if hasattr(updated_user, "user_metadata") else None,
            "avatar_url": updated_user.user_metadata.get("avatar_url") if hasattr(updated_user, "user_metadata") else None
        }

    except Exception as e:
        return {"error": str(e)}