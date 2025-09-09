from fastapi import FastAPI, HTTPException, Form, Header
from pydantic import BaseModel
from supabase import create_client, Client
import os
from dotenv import load_dotenv

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
    authorization: str = Header(...),
    avatar: UploadFile = File(None)  # Accept file upload
):
    try:
        token = authorization.split(" ")[1]  # Bearer <token>
        user = supabase.auth.get_user(token).user

        avatar_url = None
        if avatar:
            # Read file bytes
            file_bytes = await avatar.read()
            file_name = f"avatars/{user.id}/{avatar.filename}"

            # Upload to Supabase Storage (bucket called 'avatars')
            result = supabase.storage.from_('avatars').upload(file_name, file_bytes)
            if result.get('error'):
                return {"error": result['error']['message']}
            
            # Get public URL
            avatar_url = supabase.storage.from_('avatars').get_public_url(file_name)
        
        # Update metadata
        data = {"name": name}
        if avatar_url:
            data["avatar_url"] = avatar_url

        updated_user = supabase.auth.update_user({"data": data})

        return {
            "message": "Profile updated",
            "email": updated_user.user.email,
            "name": updated_user.user.user_metadata.get("name"),
            "avatar_url": updated_user.user.user_metadata.get("avatar_url")
        }
    except Exception as e:
        return {"error": str(e)}