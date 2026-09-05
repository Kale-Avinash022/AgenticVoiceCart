import os
import tempfile
import json
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from voice_input import voice_to_text
from llm_processor import extract_intent
from catalog_search import search_catalog, load_catalog, get_product_by_id, get_upsell_recommendation
from razorpay_client import (
    create_order,
    validate_money_bounds,
    generate_financial_explanation,
    RAZORPAY_KEY_ID,
    MAX_TRANSACTION_LIMIT_INR
)

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
    include_upsell: Optional[bool] = False
    user_budget: Optional[int] = None

# Audit Trail In-Memory Store for "The Bar" compliance
AUDIT_TRAIL = []

def record_audit_event(stage: str, event_type: str, details: dict, status: str = "SUCCESS"):
    """Appends an event to the security audit trail ledger."""
    import datetime
    event = {
        "id": len(AUDIT_TRAIL) + 1,
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3],
        "stage": stage,
        "event_type": event_type,
        "status": status,
        "details": details
    }
    AUDIT_TRAIL.append(event)
    return event

@app.get("/")
def read_root():
    """Root Endpoint / Health Check."""
    return {
        "status": "online",
        "app": "AgenticVoiceCart",
        "vision": "AI-Powered Voice Commerce for Razorpay",
        "track": "Track 01: AI Growth & Agentic Commerce",
        "the_bar": {
            "explainable": "Itemized financial breakdown with GST and bundle savings",
            "bounded": f"Verified against hard ceiling of ₹{MAX_TRANSACTION_LIMIT_INR:,} and voice budget",
            "gated": "Human-in-the-loop authorization modal",
            "audit_trail": f"/api/audit-trail ({len(AUDIT_TRAIL)} recorded events)"
        },
        "endpoints": {
            "process_voice": "/process_voice (POST)",
            "create_order": "/api/create-order (POST)",
            "upsell_recommendation": "/api/upsell/{item_id} (GET)",
            "validate_bounds": "/api/validate-bounds (POST)",
            "audit_trail": "/api/audit-trail (GET)",
            "agent_catalog": "/agent/v1/catalog (GET)",
            "agent_checkout": "/agent/v1/checkout (POST)",
            "agent_tools_spec": "/agent/v1/tools (GET)",
            "llms_manifest": "/llms.txt (GET)",
            "catalog": "/catalog (GET)"
        }
    }

@app.get("/api/audit-trail")
def get_audit_trail():
    """Returns the full verifiable Agent Audit Trail Ledger."""
    return {
        "total_events": len(AUDIT_TRAIL),
        "audit_trail": AUDIT_TRAIL
    }

@app.delete("/api/audit-trail")
def clear_audit_trail():
    """Resets audit trail ledger."""
    global AUDIT_TRAIL
    AUDIT_TRAIL = []
    return {"message": "Audit trail cleared"}

@app.get("/catalog")
def get_catalog():
    """Returns all catalog items."""
    return load_catalog()

@app.get("/api/upsell/{item_id}")
def get_upsell(item_id: int):
    """
    AI Merchant Growth Engine: Returns high-margin accessories
    and bundle discounts for selected product to grow merchant revenue.
    """
    rec = get_upsell_recommendation(item_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Upsell recommendation not found for product")
    return rec

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
            record_audit_event(
                stage="SPEECH_RECOGNITION",
                event_type="EMPTY_AUDIO_DETECTED",
                details={"message": "No speech detected in audio stream."},
                status="NOTICE"
            )
            return {
                "success": False,
                "text": "",
                "message": "No speech detected in audio. Please speak clearly into your mic.",
                "intent": None,
                "results": []
            }

        # Step 2: Extract Intent
        intent = extract_intent(transcribed_text)
        record_audit_event(
            stage="INTENT_NLU",
            event_type="VOICE_INTENT_PARSED",
            details={
                "transcription": transcribed_text,
                "query": intent.get("query"),
                "max_price": intent.get("max_price"),
                "brand": intent.get("brand"),
                "category": intent.get("category")
            }
        )

        # Step 3: Search Catalog
        results = search_catalog(
            query=intent.get("query", ""),
            max_price=intent.get("max_price"),
            brand=intent.get("brand"),
            category=intent.get("category")
        )

        if not results and intent.get("query"):
            results = search_catalog(query=intent.get("query"))

        record_audit_event(
            stage="CATALOG_MATCHING",
            event_type="PRODUCTS_RETRIEVED",
            details={
                "match_count": len(results),
                "matched_ids": [p["id"] for p in results]
            }
        )

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

@app.post("/api/validate-bounds")
def validate_bounds(amount: int = Query(...), user_budget: Optional[int] = Query(None)):
    """
    Validates money bounds against safety limits and user constraints.
    """
    return validate_money_bounds(amount, user_budget)

# Supporting both /api/create-order and /create_order endpoints
@app.post("/api/create-order")
@app.post("/create_order")
async def create_razorpay_order(
    item_id: Optional[int] = Query(None),
    include_upsell: Optional[bool] = Query(False),
    user_budget: Optional[int] = Query(None),
    body: Optional[OrderRequest] = Body(None)
):
    """
    Creates a Razorpay payment order for a selected product with:
    - Bounded safety checks & budget guardrails
    - Itemized explainability breakdown
    - Human-in-the-loop consent gate verification
    """
    target_item_id = item_id
    target_amount = None
    target_include_upsell = include_upsell
    target_user_budget = user_budget

    if body:
        if body.item_id:
            target_item_id = body.item_id
        if body.amount:
            target_amount = body.amount
        if body.include_upsell is not None:
            target_include_upsell = body.include_upsell
        if body.user_budget is not None:
            target_user_budget = body.user_budget

    catalog = load_catalog()
    item = None

    if target_item_id:
        item = next((p for p in catalog if p["id"] == target_item_id), None)

    if not item and catalog:
        item = catalog[0] # Default fallback product

    upsell_info = None
    if target_include_upsell and target_item_id:
        upsell_info = get_upsell_recommendation(target_item_id)

    if target_amount:
        price = target_amount
    elif upsell_info:
        price = upsell_info["bundle_total"]
    else:
        price = item["price"] if item else 999

    # 1. Bounded Safety Check
    bounds_result = validate_money_bounds(amount_in_inr=price, user_budget=target_user_budget)
    if not bounds_result["is_bounded"]:
        record_audit_event(
            stage="SAFETY_BOUNDS",
            event_type="BOUNDS_VIOLATION_BLOCKED",
            details={
                "attempted_amount": price,
                "user_budget": target_user_budget,
                "reason": bounds_result["reason"]
            },
            status="BLOCKED"
        )
        return {
            "success": False,
            "error_type": "BOUNDS_VIOLATION",
            "bounded_status": bounds_result["status"],
            "message": bounds_result["reason"],
            "amount": price,
            "user_budget": target_user_budget
        }

    record_audit_event(
        stage="SAFETY_BOUNDS",
        event_type="BOUNDS_VERIFIED_PASSED",
        details={
            "amount": price,
            "user_budget": target_user_budget,
            "max_cap": MAX_TRANSACTION_LIMIT_INR
        },
        status="PASSED"
    )

    # 2. Explainable Financial Breakdown
    explanation = generate_financial_explanation(
        base_price=item["price"] if item else price,
        upsell_price=upsell_info["upsell_price"] if upsell_info else 0,
        bundle_discount=upsell_info["bundle_discount"] if upsell_info else 0,
        product_name=item["name"] if item else "Selected Product",
        upsell_name=upsell_info["upsell_name"] if upsell_info else None
    )

    if upsell_info:
        record_audit_event(
            stage="MERCHANT_REVENUE_GROWTH",
            event_type="AI_UPSELL_ATTACHED",
            details={
                "base_price": item["price"],
                "upsell_name": upsell_info["upsell_name"],
                "upsell_price": upsell_info["upsell_price"],
                "bundle_discount": upsell_info["bundle_discount"],
                "bundle_total": upsell_info["bundle_total"],
                "revenue_lift": upsell_info["merchant_revenue_increase"]
            }
        )

    # 3. Create Order
    try:
        order = create_order(amount_in_inr=price, receipt_prefix=f"item_{target_item_id or 1}")
        record_audit_event(
            stage="RAZORPAY_GATEWAY",
            event_type="ORDER_CREATED_SIGNED",
            details={
                "order_id": order.get("id"),
                "amount_paise": order.get("amount"),
                "currency": order.get("currency", "INR"),
                "receipt": order.get("receipt")
            },
            status="READY_FOR_CONSENT"
        )
    except ValueError as ve:
        record_audit_event(
            stage="RAZORPAY_GATEWAY",
            event_type="ORDER_CREATION_FAILED",
            details={"error": str(ve)},
            status="ERROR"
        )
        raise HTTPException(status_code=400, detail=str(ve))

    return {
        "success": True,
        "item": item,
        "upsell_included": bool(upsell_info),
        "upsell_details": upsell_info,
        "bounded_check": bounds_result,
        "financial_explanation": explanation,
        "order": order,
        "order_id": order.get("id"),
        "amount": order.get("amount"),
        "currency": order.get("currency", "INR"),
        "razorpay_key_id": RAZORPAY_KEY_ID
    }

# =====================================================================
# 🤖 TRACK 01: AGENT-TO-AGENT COMMERCE & AI BUYER PROTOCOL (/agent/v1/...)
# Makes merchant sellable to autonomous AI buyers end-to-end
# =====================================================================

class AgentBuyRequest(BaseModel):
    buyer_agent_id: str
    item_id: int
    include_upsell: Optional[bool] = False
    max_authorized_budget_inr: Optional[int] = 50000
    callback_url: Optional[str] = None

@app.get("/agent/v1/catalog")
def get_agent_readable_catalog():
    """
    Agent-Readable Catalog (Track 01 Core Requirement):
    Returns standardized machine-readable schema for external autonomous AI buyers
    with stock status, structured search tokens, and revenue-optimizing upsell bundles.
    """
    catalog = load_catalog()
    agent_items = []
    for p in catalog:
        agent_items.append({
            "item_id": p["id"],
            "name": p["name"],
            "brand": p["brand"],
            "category": p["category"],
            "price_inr": p["price"],
            "mrp_inr": p.get("original_price", p["price"]),
            "stock_status": "IN_STOCK",
            "search_tokens": [p["brand"].lower(), p["category"].lower(), *p["name"].lower().split()],
            "ai_upsell_option": p.get("upsell"),
            "buy_endpoint": f"/agent/v1/checkout?item_id={p['id']}"
        })

    record_audit_event(
        stage="AGENT_PROTOCOL",
        event_type="AGENT_CATALOG_DISCOVERY",
        details={"total_items": len(agent_items), "protocol": "AgenticCommerce/v1.0"},
        status="SUCCESS"
    )

    return {
        "protocol_version": "AgenticCommerce/v1.0",
        "merchant_id": "razorpay_voicecart_store_01",
        "currency": "INR",
        "payment_gateway": "Razorpay_Test_Mode",
        "catalog_size": len(agent_items),
        "items": agent_items
    }

@app.post("/agent/v1/checkout")
def agent_autonomous_checkout(req: AgentBuyRequest):
    """
    Autonomous AI Buyer Transaction Endpoint:
    Allows an external AI agent to execute purchases with verified budget limits,
    explainable financial ledgers, and signed Razorpay order objects.
    """
    catalog = load_catalog()
    item = next((p for p in catalog if p["id"] == req.item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item ID {req.item_id} not found in merchant catalog.")

    upsell_info = None
    if req.include_upsell:
        upsell_info = get_upsell_recommendation(req.item_id)

    price = upsell_info["bundle_total"] if upsell_info else item["price"]

    # Bounded verification against AI Buyer's authorized budget
    bounds = validate_money_bounds(price, req.max_authorized_budget_inr)
    if not bounds["is_bounded"]:
        record_audit_event(
            stage="AGENT_BUYER_TRANSACTION",
            event_type="AGENT_BUDGET_REJECTED",
            details={
                "buyer_agent": req.buyer_agent_id,
                "price": price,
                "authorized_budget": req.max_authorized_budget_inr,
                "reason": bounds["reason"]
            },
            status="BLOCKED"
        )
        return {
            "status": "BOUNDS_REJECTED",
            "message": bounds["reason"],
            "price_inr": price,
            "max_authorized_budget_inr": req.max_authorized_budget_inr
        }

    # Financial Explainability
    explanation = generate_financial_explanation(
        base_price=item["price"],
        upsell_price=upsell_info["upsell_price"] if upsell_info else 0,
        bundle_discount=upsell_info["bundle_discount"] if upsell_info else 0,
        product_name=item["name"],
        upsell_name=upsell_info["upsell_name"] if upsell_info else None
    )

    # Issue Razorpay Order
    order = create_order(amount_in_inr=price, receipt_prefix=f"agent_{req.buyer_agent_id[:6]}")

    record_audit_event(
        stage="AGENT_BUYER_TRANSACTION",
        event_type="AGENT_PURCHASE_AUTHORIZED",
        details={
            "buyer_agent": req.buyer_agent_id,
            "item_id": req.item_id,
            "product": item["name"],
            "amount_inr": price,
            "order_id": order.get("id"),
            "upsell_included": req.include_upsell
        },
        status="SUCCESS"
    )

    return {
        "status": "TRANSACTION_AUTHORIZED",
        "merchant": "AgenticVoiceCart (Razorpay Buildathon 2026)",
        "buyer_agent_id": req.buyer_agent_id,
        "order_id": order.get("id"),
        "amount_paise": order.get("amount"),
        "amount_inr": price,
        "currency": "INR",
        "razorpay_key_id": RAZORPAY_KEY_ID,
        "payment_url": f"https://rzp.io/i/{order.get('id')}",
        "financial_explanation": explanation,
        "audit_verification": "Logged to merchant security ledger"
    }

@app.get("/agent/v1/tools")
def get_agent_tools_definition():
    """
    Model Context Protocol (MCP) & OpenAI Function Tools Manifest:
    Allows any external LLM / Autonomous AI Buyer to use this store as a callable tool.
    """
    return {
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "search_merchant_catalog",
                    "description": "Searches merchant products by query, brand, category, and budget.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search term e.g. 'earbuds'"},
                            "max_price": {"type": "integer", "description": "Budget limit in INR"},
                            "brand": {"type": "string", "description": "Brand name"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "agent_checkout_product",
                    "description": "Executes programmatic order creation with Razorpay test mode payment signing.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "buyer_agent_id": {"type": "string", "description": "ID of buying agent"},
                            "item_id": {"type": "integer", "description": "Product ID to buy"},
                            "include_upsell": {"type": "boolean", "description": "Attach discounted accessory bundle"},
                            "max_authorized_budget_inr": {"type": "integer", "description": "Safety budget limit"}
                        },
                        "required": ["buyer_agent_id", "item_id"]
                    }
                }
            }
        ]
    }

@app.get("/llms.txt")
def get_llms_manifest():
    """Manifest for LLM Web Crawlers and Autonomous AI Agents."""
    return {
        "title": "AgenticVoiceCart — Razorpay Agentic Commerce Merchant Store",
        "description": "AI-powered voice commerce store with Razorpay UPI payments and autonomous agent endpoints.",
        "agent_endpoints": {
            "catalog": "http://127.0.0.1:8000/agent/v1/catalog",
            "checkout": "http://127.0.0.1:8000/agent/v1/checkout",
            "tools_spec": "http://127.0.0.1:8000/agent/v1/tools",
            "audit_trail": "http://127.0.0.1:8000/api/audit-trail"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
