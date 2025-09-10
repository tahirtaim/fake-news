from fastapi import APIRouter, Form, Header, HTTPException, Depends
from typing import Optional
from app.services.supabase_client import supabase
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch

router = APIRouter()

model_name = "YerayEsp/FakeBERTa"
classifier = pipeline("text-classification", model=model_name, tokenizer=model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
label_map = {"LABEL_0": "FAKE", "LABEL_1": "REAL"}

async def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    token = authorization.replace("Bearer ", "")
    try:

        user = supabase.auth.get_user(token)
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

def predict_text(headline=None, body=None):
    if headline and body:
        text = headline + " " + body
    elif headline:
        text = headline
    elif body:
        text = body
    else:
        return {"error": "No text provided"}

    result = classifier(text)[0]
    label = label_map.get(result['label'], result['label'])

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

@router.post("/predict")
async def predict(
    headline: Optional[str] = Form(None),
    body: Optional[str] = Form(None),
    user = Depends(verify_token)
):
    if not headline and not body:
        raise HTTPException(status_code=400, detail="Either headline or body must be provided")
    
    result = predict_text(headline=headline, body=body)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {
        "label": result["label"],
        "fake_score": result["fake_score"],
        "real_score": result["real_score"]
    }