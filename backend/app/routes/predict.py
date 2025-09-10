from fastapi import APIRouter, Header, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from app.services.supabase_client import supabase
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch

router = APIRouter()

# ----------------- Load model -----------------
model_name = "YerayEsp/FakeBERTa"
classifier = pipeline("text-classification", model=model_name, tokenizer=model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
label_map = {"LABEL_0": "FAKE", "LABEL_1": "REAL"}

# ----------------- Pydantic model for JSON request -----------------
class PredictRequest(BaseModel):
    headline: Optional[str] = None
    body: Optional[str] = None

# ----------------- Auth dependency -----------------
async def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    token = authorization.replace("Bearer ", "")
    try:
        user = supabase.auth.get_user(token).user
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

# ----------------- Prediction helper -----------------
def predict_text(headline=None, body=None):
    if headline and body:
        text = headline + " " + body
    elif headline:
        text = headline
    elif body:
        text = body
    else:
        return {"error": "No text provided"}

    # Simple classifier
    result = classifier(text)[0]
    label = label_map.get(result['label'], result['label'])

    # Compute probabilities
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    outputs = model(**inputs)
    probs = torch.nn.functional.softmax(outputs.logits, dim=-1)[0].detach()

    fake_score = float(f"{probs[0]:.4f}")
    real_score = float(f"{probs[1]:.4f}")

    return {
        "label": label,
        "fake_score": fake_score,
        "real_score": real_score
    }

# ----------------- Predict endpoint -----------------
@router.post("/predict")
async def predict(request: PredictRequest, user = Depends(verify_token)):
    if not request.headline and not request.body:
        raise HTTPException(status_code=400, detail="Either headline or body must be provided")
    
    result = predict_text(headline=request.headline, body=request.body)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "label": result["label"],
        "fake_score": result["fake_score"],
        "real_score": result["real_score"]
    }
