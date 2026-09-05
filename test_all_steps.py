import sys
import os
import json

# Set standard UTF-8 stdout
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")

import main
import catalog_search
import razorpay_client
from fastapi.testclient import TestClient

client = TestClient(main.app)

def run_tests():
    print("=====================================================")
    print("🧪 RUNNING COMPREHENSIVE TEST SUITE (STEPS 1 TO 5)")
    print("=====================================================")

    # Clear audit trail for clean test state
    client.delete("/api/audit-trail")

    # --- TEST 1: Step 1 AI Upsell & Revenue Growth Engine ---
    print("\n[1/5] Testing Step 1: AI Upsell & Merchant Revenue Growth...")
    upsell = catalog_search.get_upsell_recommendation(1)
    assert upsell is not None, "Upsell for item 1 should exist"
    assert upsell["bundle_total"] == 1498, f"Expected 1498, got {upsell['bundle_total']}"
    print(f"  ✓ catalog_search.get_upsell_recommendation(1): {upsell['upsell_name']} (Bundle Total: ₹{upsell['bundle_total']})")

    res_upsell_api = client.get("/api/upsell/1")
    assert res_upsell_api.status_code == 200, "API /api/upsell/1 failed"
    print(f"  ✓ GET /api/upsell/1 HTTP 200: {res_upsell_api.json()['merchant_revenue_increase']} AOV Lift")

    res_bundle_order = client.post("/api/create-order", json={"item_id": 1, "include_upsell": True})
    assert res_bundle_order.status_code == 200
    data_bundle = res_bundle_order.json()
    assert data_bundle["success"] is True
    assert data_bundle["amount"] == 149800, f"Expected 149800 paise, got {data_bundle['amount']}"
    print(f"  ✓ POST /api/create-order (Bundled Upsell): Created Razorpay order for ₹{data_bundle['amount']/100}")

    # --- TEST 2: Step 2 Bounded & Explainable Guardrails ---
    print("\n[2/5] Testing Step 2: Bounded Safety Limits & Financial Explainability...")
    # Normal bound pass
    b1 = razorpay_client.validate_money_bounds(1299, 2000)
    assert b1["is_bounded"] is True
    print("  ✓ Safety Bound Normal Check (₹1,299 <= ₹2,000 budget): PASSED")

    # User budget overrun
    b2 = razorpay_client.validate_money_bounds(24900, 2000)
    assert b2["is_bounded"] is False
    assert b2["status"] == "REJECTED_USER_BUDGET_EXCEEDED"
    print("  ✓ Safety Bound Budget Overrun (₹24,900 vs ₹2,000 budget): REJECTED_USER_BUDGET_EXCEEDED (PASSED)")

    # Hard cap limit
    b3 = razorpay_client.validate_money_bounds(60000)
    assert b3["is_bounded"] is False
    assert b3["status"] == "REJECTED_MAX_CAP_EXCEEDED"
    print("  ✓ Hard Safety Ceiling Guardrail (₹60,000 > ₹50,000 cap): REJECTED_MAX_CAP_EXCEEDED (PASSED)")

    # Financial Explainability
    expl = razorpay_client.generate_financial_explanation(1299, 249, 50, "Boat Earbuds", "Silicone Case")
    assert len(expl["breakdown"]) == 3
    assert "18%" in expl["tax_breakdown"]["gst_rate"]
    print("  ✓ Financial Explainability breakdown generated with itemized GST & savings.")

    # --- TEST 3: Step 3 Security Audit Trail ---
    print("\n[3/5] Testing Step 3: Verifiable Security Audit Trail Ledger...")
    res_audit = client.get("/api/audit-trail")
    assert res_audit.status_code == 200
    audit_data = res_audit.json()
    assert audit_data["total_events"] > 0
    print(f"  ✓ GET /api/audit-trail: Returned {audit_data['total_events']} recorded events")
    for ev in audit_data["audit_trail"]:
        print(f"     • [{ev['timestamp']}] Stage: {ev['stage']} -> {ev['event_type']} ({ev['status']})")

    # --- TEST 4: Step 4 Graceful Failure Handling & Recovery ---
    print("\n[4/5] Testing Step 4: Graceful Failure Handling & Recovery...")
    # Test Budget Breach Rejection Graceful Handling
    res_breach = client.post("/api/create-order", json={"item_id": 2, "user_budget": 2000}) # Sony WH-1000XM5 ₹29990 vs budget 2000
    assert res_breach.status_code == 200
    breach_data = res_breach.json()
    assert breach_data["success"] is False
    assert breach_data["error_type"] == "BOUNDS_VIOLATION"
    assert "exceeds user's stated voice budget" in breach_data["message"]
    print("  ✓ Budget Overrun Failure Mode: Agent safely intercepted and returned graceful rejection message.")

    # Verify Audit Trail recorded the blocked failure event
    res_audit_after = client.get("/api/audit-trail")
    latest_event = res_audit_after.json()["audit_trail"][-1]
    assert latest_event["stage"] == "SAFETY_BOUNDS"
    assert latest_event["event_type"] == "BOUNDS_VIOLATION_BLOCKED"
    print(f"  ✓ Audit Trail Logged Failure Event: {latest_event['event_type']} (Status: {latest_event['status']})")

    # --- TEST 5: Step 5 Agent-Readable Catalog & AI Buyer Protocol ---
    print("\n[5/5] Testing Step 5: Agent-to-Agent Commerce Protocol (/agent/v1/...)...")
    # 5.1 Agent Catalog Schema
    res_agent_cat = client.get("/agent/v1/catalog")
    assert res_agent_cat.status_code == 200
    agent_cat_data = res_agent_cat.json()
    assert agent_cat_data["protocol_version"] == "AgenticCommerce/v1.0"
    assert len(agent_cat_data["items"]) > 0
    print(f"  ✓ GET /agent/v1/catalog: Schema verified with {len(agent_cat_data['items'])} agent-readable products.")

    # 5.2 Agent Tools Spec (MCP Manifest)
    res_tools = client.get("/agent/v1/tools")
    assert res_tools.status_code == 200
    tools_data = res_tools.json()
    assert "tools" in tools_data and len(tools_data["tools"]) == 2
    print("  ✓ GET /agent/v1/tools: MCP & OpenAI function definitions valid.")

    # 5.3 Agent Autonomous Checkout (Programmatic purchase by AI buyer)
    agent_payload = {
        "buyer_agent_id": "ai_buyer_agent_gemini_99",
        "item_id": 1,
        "include_upsell": True,
        "max_authorized_budget_inr": 5000
    }
    res_agent_buy = client.post("/agent/v1/checkout", json=agent_payload)
    assert res_agent_buy.status_code == 200
    agent_buy_data = res_agent_buy.json()
    assert agent_buy_data["status"] == "TRANSACTION_AUTHORIZED"
    assert agent_buy_data["amount_inr"] == 1498
    assert "payment_url" in agent_buy_data
    print(f"  ✓ POST /agent/v1/checkout: Autonomous AI Buyer completed purchase. Order ID: {agent_buy_data['order_id']}, Total: ₹{agent_buy_data['amount_inr']}")

    print("\n=====================================================")
    print("🎉 ALL TESTS FOR STEPS 1 TO 5 PASSED WITH 100% SUCCESS!")
    print("=====================================================")

if __name__ == "__main__":
    run_tests()
