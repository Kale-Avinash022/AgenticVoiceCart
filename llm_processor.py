import re
import json

def extract_intent(text: str) -> dict:
    """
    Extracts shopping intent from transcribed user text.
    
    Args:
        text (str): Transcribed speech input (e.g. "Show me wireless earbuds under 2000 rupees").
        
    Returns:
        dict: {
            "query": str,        # Product search query (e.g. "wireless earbuds")
            "max_price": int/None, # Maximum price in INR (e.g. 2000)
            "brand": str/None,   # Specified brand (e.g. "Sony", "Boat", "Apple")
            "category": str/None # Category (e.g. "earbuds", "headphones", "smartwatch")
        }
    """
    if not text or not text.strip():
        return {
            "query": "",
            "max_price": None,
            "brand": None,
            "category": None
        }

    clean_text = text.lower().strip()

    # 1. Brand Extraction
    known_brands = [
        "sony", "boat", "apple", "samsung", "jbl", "noise",
        "realme", "oneplus", "boult", "sennheiser", "ptron"
    ]
    detected_brand = None
    for brand in known_brands:
        if re.search(r'\b' + re.escape(brand) + r'\b', clean_text):
            detected_brand = brand.title()
            if detected_brand == "Boat":
                detected_brand = "Boat"
            break

    # 2. Price Extraction (matches: under 2000, below 5000, less than 1500, rs 2000, 2000 rupees, ₹2000)
    max_price = None
    price_patterns = [
        r'(?:under|below|less than|within|around|budget of|max|upto|up to)\s*(?:rs\.?|inr|₹)?\s*(\d+)',
        r'(?:rs\.?|inr|₹)\s*(\d+)',
        r'(\d+)\s*(?:rupees|rs|inr)'
    ]
    for pattern in price_patterns:
        match = re.search(pattern, clean_text)
        if match:
            max_price = int(match.group(1))
            break

    # 3. Category Extraction
    categories = {
        "earbuds": ["earbuds", "earbud", "tws", "airpods", "earphones", "earphone", "buds", "airdopes"],
        "headphones": ["headphones", "headphone", "headset", "over ear"],
        "smartwatch": ["smartwatch", "smart watch", "watch", "fitness band"],
        "speakers": ["speaker", "speakers", "soundbar", "bluetooth speaker"]
    }
    
    detected_category = None
    for cat, keywords in categories.items():
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', clean_text):
                detected_category = cat
                break
        if detected_category:
            break

    # 4. Product Search Query Normalization
    # Strip common conversational filler words
    words_to_strip = [
        r'\bshow me\b', r'\bfind me\b', r'\bsearch for\b', r'\blooking for\b', r'\bi want\b',
        r'\bbuy\b', r'\bget\b', r'\bshow\b', r'\bunder\b', r'\bbelow\b', r'\bless than\b',
        r'\bwithin\b', r'\bmax\b', r'\brupees\b', r'\brs\b', r'\binr\b', r'₹'
    ]
    if max_price:
        words_to_strip.append(str(max_price))

    query_builder = clean_text
    for word in words_to_strip:
        query_builder = re.sub(word, '', query_builder, flags=re.IGNORECASE)

    # Clean whitespace and trailing punctuation
    query_builder = re.sub(r'[^\w\s]', '', query_builder)
    query_builder = ' '.join(query_builder.split()).strip()

    # Fallbacks
    if not query_builder and detected_category:
        query_builder = detected_category
    elif not query_builder:
        query_builder = clean_text

    return {
        "query": query_builder,
        "max_price": max_price,
        "brand": detected_brand,
        "category": detected_category
    }

if __name__ == "__main__":
    test_queries = [
        "Show me wireless earbuds under 2000 rupees",
        "Show me Sony headphones below 5000",
        "Apple airpods under 15000 inr",
        "Boat airdopes under 1000",
        "I want a smartwatch under 3000"
    ]
    
    print("\n--- LLM Intent Processor Verification ---")
    for q in test_queries:
        intent = extract_intent(q)
        print(f"\nInput:  '{q}'")
        print(f"Parsed: {json.dumps(intent, indent=2)}")
    print("\n------------------------------------------")
