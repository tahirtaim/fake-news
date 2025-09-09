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
    Update logged-in user's metadata
    """
    try:
        # Extract JWT token
        token = authorization.split(" ")[1]  # Bearer <token>

        # Get user info
        user = supabase.auth.get_user(token).user
        
        avatar_url = None
        
        # Handle avatar upload if provided
        if avatar and avatar.filename:
            # Read file content
            file_content = await avatar.read()
            
            # Create a unique file path
            import uuid
            file_ext = avatar.filename.split(".")[-1]
            file_path = f"{uuid.uuid4()}.{file_ext}"
            
            # Upload file to Supabase Storage
            supabase.storage.from_("avatars").upload(
                path=file_path,
                file=file_content,
                file_options={"content-type": avatar.content_type}
            )
            
            # Get public URL for the uploaded file
            avatar_url = supabase.storage.from_("avatars").get_public_url(file_path)
        
        # Prepare update data
        update_data = {"name": name} if name else {}
        if avatar_url:
            update_data["avatar_url"] = avatar_url
            
        # Only update if we have data to update
        if update_data:
            # Update metadata
            updated_user = supabase.auth.update_user({
                "data": update_data
            }, token)
            
            return {
                "message": "Profile updated",
                "email": updated_user.user.email,
                "name": updated_user.user.user_metadata.get("name"),
                "avatar_url": updated_user.user.user_metadata.get("avatar_url")
            }
        else:
            return {"message": "No changes to update"}

    except Exception as e:
        return {"error": str(e)}