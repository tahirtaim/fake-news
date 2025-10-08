from fastapi import APIRouter, Form, HTTPException, status
from app.services.supabase_client import supabase

router = APIRouter()

# ----------------- Signup -----------------
@router.post("/signup")
def signup(
    email: str = Form(...),
    password: str = Form(...),
    name: str = Form(None),
    avatar: str = Form(None)
):
    """
    Create a new user account in Supabase.
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

        # Check if user was created successfully
        if not result.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user account"
            )

        return {
            "message": "User created successfully",
            "email": result.user.email,
            "access_token": result.session.access_token if result.session else None,
            "avatar_url": result.user.user_metadata.get("avatar_url")
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ----------------- Login -----------------
@router.post("/login")
def login(
    email: str = Form(...),
    password: str = Form(...)
):
    """
    Authenticate an existing user and return an access token.
    Returns 404 if the email or password is incorrect.
    """
    try:
        result = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        # If session is not returned, credentials are invalid
        if not result.session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid email or password"
            )

        # Successful login
        return {
            "message": "Login successful",
            "email": result.user.email,
            "name": result.user.user_metadata.get("name"),
            "avatar_url": result.user.user_metadata.get("avatar_url"),
            "access_token": result.session.access_token
        }

    except Exception as e:
        error_msg = str(e)

        # Handle known invalid login attempts gracefully
        if "Invalid login credentials" in error_msg or "Invalid credentials" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid email or password"
            )

        # Fallback for unexpected Supabase or internal errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {error_msg}"
        )

