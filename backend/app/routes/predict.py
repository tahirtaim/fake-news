from fastapi import APIRouter, Header, HTTPException, Depends, Form
from typing import Optional
from app.services.supabase_client import supabase
from datetime import datetime

# Import from connect_fast_api.py
from transformers import BertTokenizer, TFBertForSequenceClassification
import tensorflow as tf
import numpy as np

router = APIRouter()

# ----------------- Load model -----------------
# Global variables from connect_fast_api.py
model = None
tokenizer = None
class_labels = ["unrelated", "discuss", "agree", "disagree"]

relationship_info = {
    "unrelated": {
        "description": "The article does not discuss the headline topic",
        "color": "#6B7280",
        "is_related": False
    },
    "discuss": {
        "description": "The article discusses the headline topic but takes no position",
        "color": "#3B82F6",
        "is_related": True
    },
    "agree": {
        "description": "The article agrees with the headline claim",
        "color": "#10B981",
        "is_related": True
    },
    "disagree": {
        "description": "The article disagrees with the headline claim",
        "color": "#EF4444",
        "is_related": True
    }
}

# ----------------- Model loading function -----------------
def load_model():
    global model, tokenizer
    if model is None or tokenizer is None:
        model_name = "shamim748/shamim-fake-news-bert"
        print("🚀 Loading model from Hugging Face Hub...")
        tokenizer = BertTokenizer.from_pretrained(model_name)
        model = TFBertForSequenceClassification.from_pretrained(model_name)
        print("✅ Model loaded successfully!")

# ----------------- Format text function -----------------
def format_fnc_text(headline, body):
    """Format text for FNC-1 task"""
    return f"HEADLINE: {headline} ARTICLE: {body}"

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

# ----------------- Prediction function -----------------
def predict_text(headline="", body=""):
    # Load model if not loaded
    load_model()
    
    # Format the text for prediction
    text = format_fnc_text(headline, body)
    
    # Tokenize and predict
    inputs = tokenizer(text, truncation=True, padding=True, max_length=256, return_tensors="tf")
    outputs = model(inputs)
    probs = tf.nn.softmax(outputs.logits, axis=-1).numpy()[0]
    predicted_class = int(np.argmax(probs))
    predicted_label = class_labels[predicted_class]
    relationship = relationship_info[predicted_label]
    max_prob = float(probs[predicted_class])

    # Confidence threshold handling
    confidence_threshold = 0.7
    was_overridden = max_prob < confidence_threshold
    if was_overridden:
        predicted_label = "discuss"
        predicted_class = 1
        relationship = relationship_info["discuss"]

    return {
        "probabilities": probs.tolist(),
        "predictedClass": predicted_class,
        "predictedLabel": predicted_label,
        "relationship": predicted_label,
        "description": relationship["description"],
        "color": relationship["color"],
        "confidence": max_prob,
        "isRelated": relationship["is_related"],
        "wasOverridden": was_overridden,
        "timestamp": datetime.now().isoformat()
    }

# ----------------- Predict endpoint with form data -----------------
@router.post("/predict")
async def predict(
    headline: Optional[str] = Form(None),
    body: Optional[str] = Form(None),
    user = Depends(verify_token)
):
    # Ensure at least one of headline or body is provided
    if not headline and not body:
        raise HTTPException(status_code=400, detail="Either headline or body must be provided")
    
    # Use empty string for missing fields
    headline = headline or ""
    body = body or ""
    
    # Get prediction result
    result = predict_text(headline=headline, body=body)
    
    return result

# from fastapi import APIRouter, Header, HTTPException, Depends
# from pydantic import BaseModel
# from typing import Optional
# from app.services.supabase_client import supabase
# from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
# import torch

# router = APIRouter()

# # ----------------- Load model -----------------
# model_name = "YerayEsp/FakeBERTa"
# classifier = pipeline("text-classification", model=model_name, tokenizer=model_name)
# tokenizer = AutoTokenizer.from_pretrained(model_name)
# model = AutoModelForSequenceClassification.from_pretrained(model_name)
# label_map = {"LABEL_0": "FAKE", "LABEL_1": "REAL"}

# # ----------------- Pydantic model for JSON request -----------------
# class PredictRequest(BaseModel):
#     headline: Optional[str] = None
#     body: Optional[str] = None

# # ----------------- Auth dependency -----------------
# async def verify_token(authorization: str = Header(None)):
#     if not authorization or not authorization.startswith("Bearer "):
#         raise HTTPException(status_code=401, detail="Invalid authentication token")
    
#     token = authorization.replace("Bearer ", "")
#     try:
#         user = supabase.auth.get_user(token).user
#         return user
#     except Exception:
#         raise HTTPException(status_code=401, detail="Invalid authentication token")

# # ----------------- Prediction helper -----------------
# def predict_text(headline=None, body=None):
#     if headline and body:
#         text = headline + " " + body
#     elif headline:
#         text = headline
#     elif body:
#         text = body
#     else:
#         return {"error": "No text provided"}

#     # Simple classifier
#     result = classifier(text)[0]
#     label = label_map.get(result['label'], result['label'])

#     # Compute probabilities
#     inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
#     outputs = model(**inputs)
#     probs = torch.nn.functional.softmax(outputs.logits, dim=-1)[0].detach()

#     fake_score = float(f"{probs[0]:.4f}")
#     real_score = float(f"{probs[1]:.4f}")

#     return {
#         "label": label,
#         "fake_score": fake_score,
#         "real_score": real_score
#     }

# # ----------------- Predict endpoint -----------------
# @router.post("/predict")
# async def predict(request: PredictRequest, user = Depends(verify_token)):
#     if not request.headline and not request.body:
#         raise HTTPException(status_code=400, detail="Either headline or body must be provided")
    
#     result = predict_text(headline=request.headline, body=request.body)
    
#     if "error" in result:
#         raise HTTPException(status_code=400, detail=result["error"])
    
#     return {
#         "label": result["label"],
#         "fake_score": result["fake_score"],
#         "real_score": result["real_score"]
#     }
