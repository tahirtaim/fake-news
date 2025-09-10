from fastapi import FastAPI
from app.routes import auth, profile

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello from FastAPI + Supabase"}

# Include routes
app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(profile.router, prefix="/api", tags=["User"])
