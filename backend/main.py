from fastapi import *
from pydantic import BaseModel
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import uuid

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
app = FastAPI()
@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI + Supabase"}

@app.get("/users")
def get_users():
    users = supabase.table("users").select("*").execute()
    print("Fetched users:", users.data)
    return users.data
@app.post("/signup")
def signup(email: str = Form(...), password: str = Form(...), name: str = Form(None), avatar: str = Form(None)):
    """
    Signup user using form data (email and password)
    """
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
@app.post("/login")
def login(email: str = Form(...), password: str = Form(...)):
    """
    Login user using form data and return JWT token
    """
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

@app.post("/update-profile")
async def update_profile(
    name: str = Form(None), 
    avatar: UploadFile = File(None), 
    authorization: str = Header(...)
):
    """
    Update logged-in user's metadata with enhanced security and file management
    """
    try:
        # Extract JWT token
        token = authorization.split(" ")[1]  # Bearer <token>

        # Get user info
        user = supabase.auth.get_user(token).user
        user_id = user.id
        
        avatar_url = user.user_metadata.get("avatar_url") if user.user_metadata else None
        old_avatar_path = None
        
        # Extract path from old avatar URL if it exists
        if avatar_url and "avatars/" in avatar_url:
            old_avatar_path = avatar_url.split("avatars/")[-1]
        
        # Handle file upload if avatar is provided
        if avatar:
            # Validate file type
            allowed_types = ["image/jpeg", "image/png", "image/gif"]
            if avatar.content_type not in allowed_types:
                return {"error": "Invalid file type. Only JPEG, PNG and GIF are allowed."}
                
            # Read and validate file size
            file_content = await avatar.read()
            if len(file_content) > 2_000_000:  # 2MB limit
                return {"error": "File too large. Maximum size is 2MB."}
            
            # Generate path with user ID for better organization
            file_ext = os.path.splitext(avatar.filename)[1].lower()
            file_path = f"users/{user_id}/avatar{file_ext}"
            
            # Upload to Supabase Storage
            storage_response = supabase.storage.from_("avatars").upload(
                path=file_path,
                file=file_content,
                file_options={"content-type": avatar.content_type, "upsert": True}
            )
            
            # Get public URL
            avatar_url = supabase.storage.from_("avatars").get_public_url(file_path)
            
            # Delete old avatar if it exists and is different
            if old_avatar_path and old_avatar_path != file_path:
                try:
                    supabase.storage.from_("avatars").remove([old_avatar_path])
                except Exception as e:
                    # Log error but don't fail the whole operation
                    print(f"Failed to delete old avatar: {str(e)}")

        # Update metadata with new values or keep existing ones
        update_data = {
            "data": {
                "name": name if name is not None else user.user_metadata.get("name"),
                "avatar_url": avatar_url
            }
        }

        # Update user metadata
        updated_user = supabase.auth.update_user(update_data)

        return {
            "message": "Profile updated",
            "email": updated_user.user.email,
            "name": updated_user.user.user_metadata.get("name"),
            "avatar_url": updated_user.user.user_metadata.get("avatar_url")
        }

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {"error": str(e)}