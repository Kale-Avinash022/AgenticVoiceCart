import os
import razorpay

# Razorpay Test Mode Credentials (Placeholder defaults - replaceable via environment variables or direct keys)
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_YourTestKeyId")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "YourTestSecretKey")

# "The Bar" Safety Bounds
MAX_TRANSACTION_LIMIT_INR = 50000 # Hard safety cap on autonomous agent checkouts
MIN_TRANSACTION_LIMIT_INR = 1

def validate_money_bounds(amount_in_inr: int, user_budget: int = None) -> dict:
    """
    Validates money movement against hard safety limits and user-defined budget constraints.
    Returns:
        dict: {"is_bounded": bool, "status": str, "reason": str}
    """
    if amount_in_inr <= 0 or amount_in_inr < MIN_TRANSACTION_LIMIT_INR:
        return {
            "is_bounded": False,
            "status": "REJECTED_ZERO_AMOUNT",
            "reason": f"Amount ₹{amount_in_inr} is below minimum allowed transaction limit (₹{MIN_TRANSACTION_LIMIT_INR})."
        }
        
    if amount_in_inr > MAX_TRANSACTION_LIMIT_INR:
        return {
            "is_bounded": False,
            "status": "REJECTED_MAX_CAP_EXCEEDED",
            "reason": f"Amount ₹{amount_in_inr} exceeds hard agent safety ceiling of ₹{MAX_TRANSACTION_LIMIT_INR:,}."
        }
        
    if user_budget is not None and amount_in_inr > user_budget:
        return {
            "is_bounded": False,
            "status": "REJECTED_USER_BUDGET_EXCEEDED",
            "reason": f"Amount ₹{amount_in_inr} exceeds user's stated voice budget constraint of ₹{user_budget:,}."
        }

    return {
        "is_bounded": True,
        "status": "BOUNDS_PASSED",
        "reason": f"Amount ₹{amount_in_inr} is bounded and verified within safety limits (Cap: ₹{MAX_TRANSACTION_LIMIT_INR:,})."
    }

def generate_financial_explanation(
    base_price: int,
    upsell_price: int = 0,
    bundle_discount: int = 0,
    product_name: str = "Product",
    upsell_name: str = None
) -> dict:
    """
    Generates human & agent explainability breakdown for the money movement.
    """
    subtotal = base_price + upsell_price - bundle_discount
    gst_component = round(subtotal * 0.18 / 1.18, 2) # GST included (18%)
    
    breakdown = [
        {"item": product_name, "type": "base_product", "amount": base_price}
    ]
    if upsell_name and upsell_price > 0:
        breakdown.append({"item": upsell_name, "type": "ai_upsell_addon", "amount": upsell_price})
    if bundle_discount > 0:
        breakdown.append({"item": "AI Merchant Bundle Discount", "type": "discount", "amount": -bundle_discount})

    return {
        "total_authorized_amount": subtotal,
        "currency": "INR",
        "breakdown": breakdown,
        "tax_breakdown": {
            "gst_rate": "18%",
            "gst_included_inr": gst_component,
            "net_before_tax_inr": round(subtotal - gst_component, 2)
        },
        "explainability_statement": f"Customer authorized payment of ₹{subtotal:,} for {product_name}" + 
            (f" bundled with {upsell_name} (Saved ₹{bundle_discount})." if bundle_discount > 0 else ".")
    }

def get_razorpay_client():
    """Initializes and returns Razorpay client."""
    return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

def create_order(amount_in_inr: int, currency: str = "INR", receipt_prefix: str = "order_rcptid") -> dict:
    """
    Creates a Razorpay order with bounds validation.
    
    Args:
        amount_in_inr (int): Order amount in Indian Rupees (INR).
        currency (str): Currency code (default "INR").
        receipt_prefix (str): Receipt ID prefix.
        
    Returns:
        dict: Razorpay order object or simulated order object for test mode.
    """
    bounds = validate_money_bounds(amount_in_inr)
    if not bounds["is_bounded"]:
        raise ValueError(bounds["reason"])

    amount_in_paise = int(amount_in_inr * 100) # Razorpay uses paise (1 INR = 100 paise)
    
    # Try calling Razorpay API if valid test key is configured
    try:
        if RAZORPAY_KEY_ID and not RAZORPAY_KEY_ID.startswith("rzp_test_YourTestKey"):
            client = get_razorpay_client()
            order_data = {
                "amount": amount_in_paise,
                "currency": currency,
                "receipt": f"{receipt_prefix}_101",
                "notes": {
                    "purpose": "AgenticVoiceCart Checkout"
                }
            }
            return client.order.create(data=order_data)
    except Exception as e:
        print(f"Razorpay API Notice: {e}. Falling back to Test Order Mode.")

    # Simulated Razorpay Order Object (for offline / test mode demo without real key)
    import time
    simulated_order_id = f"order_{int(time.time())}"
    return {
        "id": simulated_order_id,
        "entity": "order",
        "amount": amount_in_paise,
        "amount_paid": 0,
        "amount_due": amount_in_paise,
        "currency": currency,
        "receipt": f"{receipt_prefix}_101",
        "status": "created",
        "attempts": 0,
        "notes": {
            "purpose": "AgenticVoiceCart Voice Commerce Demo"
        },
        "created_at": int(time.time()),
        "key_id": RAZORPAY_KEY_ID
    }

if __name__ == "__main__":
    print("\n--- Razorpay Client Test ---")
    test_order = create_order(amount_in_inr=1999)
    print(f"Created Razorpay Order: {test_order['id']}")
    print(f"Amount in Paise: {test_order['amount']} paise (Rs {test_order['amount']/100})")
    print("----------------------------")
