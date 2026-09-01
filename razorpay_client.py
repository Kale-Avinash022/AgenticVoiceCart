import os
import razorpay

# Razorpay Test Mode Credentials (Placeholder defaults - replaceable via environment variables or direct keys)
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_YourTestKeyId")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "YourTestSecretKey")

def get_razorpay_client():
    """Initializes and returns Razorpay client."""
    return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

def create_order(amount_in_inr: int, currency: str = "INR", receipt_prefix: str = "order_rcptid") -> dict:
    """
    Creates a Razorpay order.
    
    Args:
        amount_in_inr (int): Order amount in Indian Rupees (INR).
        currency (str): Currency code (default "INR").
        receipt_prefix (str): Receipt ID prefix.
        
    Returns:
        dict: Razorpay order object or simulated order object for test mode.
    """
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
