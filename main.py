import os
import tempfile
import json
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from voice_input import voice_to_text
from llm_processor import extract_intent
from catalog_search import search_catalog, load_catalog
from razorpay_client import create_order, RAZORPAY_KEY_ID

app = FastAPI(
    title="AgenticVoiceCart API",
    description="AI-Powered Voice Commerce Backend for Razorpay Buildathon 2026",
    version="1.0.0"
)

# Enable CORS for frontend client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class OrderRequest(BaseModel):
    item_id: Optional[int] = None
    amount: Optional[int] = None

@app.get("/")
def read_root():
    """Root Endpoint / Health Check."""
    return {
        "status": "online",
        "app": "AgenticVoiceCart",
        "vision": "AI-Powered Voice Commerce for Razorpay",
        "endpoints": {
            "process_voice": "/process_voice (POST)",
            "create_order": "/api/create-order (POST)",
            "catalog": "/catalog (GET)"
        }
    }

@app.get("/catalog")
def get_catalog():
    """Returns all catalog items."""
    return load_catalog()

@app.post("/process_voice")
async def process_voice(audio: UploadFile = File(...)):
    """
    Processes user voice input audio file:
    1. Transcribes audio to text (Whisper)
    2. Extracts intent (LLM Processor)
    3. Searches catalog (Catalog Search Engine)
    """
    if not audio:
        raise HTTPException(status_code=400, detail="No audio file uploaded.")

    tmp_file_path = None
    try:
        suffix = ".wav"
        if audio.filename and "." in audio.filename:
            suffix = f".{audio.filename.split('.')[-1]}"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_file_path = tmp.name

        # Step 1: Voice to Text
        transcribed_text = voice_to_text(tmp_file_path)
        if not transcribed_text:
            return {
                "success": False,
                "text": "",
                "message": "No speech detected in audio. Please speak clearly into your mic.",
                "intent": None,
                "results": []
            }

        # Step 2: Extract Intent
        intent = extract_intent(transcribed_text)

        # Step 3: Search Catalog
        results = search_catalog(
            query=intent.get("query", ""),
            max_price=intent.get("max_price"),
            brand=intent.get("brand"),
            category=intent.get("category")
        )

        if not results and intent.get("query"):
            results = search_catalog(query=intent.get("query"))

        return {
            "success": True,
            "text": transcribed_text,
            "intent": intent,
            "results": results,
            "count": len(results),
            "razorpay_key_id": RAZORPAY_KEY_ID
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if tmp_file_path and os.path.exists(tmp_file_path):
            try:
                os.unlink(tmp_file_path)
            except Exception:
                pass

# Supporting both /api/create-order and /create_order endpoints
@app.post("/api/create-order")
@app.post("/create_order")
async def create_razorpay_order(
    item_id: Optional[int] = Query(None),
    body: Optional[OrderRequest] = Body(None)
):
    """
    Creates a Razorpay payment order for a selected product.
    Supports both JSON body and Query Parameters.
    """
    target_item_id = item_id
    target_amount = None

    if body:
        if body.item_id:
            target_item_id = body.item_id
        if body.amount:
            target_amount = body.amount

    catalog = load_catalog()
    item = None

    if target_item_id:
        item = next((p for p in catalog if p["id"] == target_item_id), None)

    if not item and catalog:
        item = catalog[0] # Default fallback product

    price = target_amount if target_amount else (item["price"] if item else 999)
    order = create_order(amount_in_inr=price, receipt_prefix=f"item_{target_item_id or 1}")

    return {
        "success": True,
        "item": item,
        "order": order,
        "order_id": order.get("id"),
        "amount": order.get("amount"),
        "currency": order.get("currency", "INR"),
        "razorpay_key_id": RAZORPAY_KEY_ID
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
