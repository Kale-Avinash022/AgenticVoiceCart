import json
import os

CATALOG_PATH = os.path.join(os.path.dirname(__file__), "catalog.json")

def load_catalog() -> list:
    """Loads the catalog JSON database."""
    if not os.path.exists(CATALOG_PATH):
        return []
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def search_catalog(query: str = "", max_price: int = None, brand: str = None, category: str = None) -> list:
    """
    Searches product catalog based on user intent filters.
    
    Args:
        query (str): Search term/query.
        max_price (int): Upper price limit.
        brand (str): Filter by brand.
        category (str): Filter by category.
        
    Returns:
        list: Matching product objects.
    """
    catalog = load_catalog()
    results = []

    clean_query = query.lower().strip() if query else ""
    clean_brand = brand.lower().strip() if brand else None
    clean_category = category.lower().strip() if category else None

    # Split query into keywords
    keywords = [k for k in clean_query.split() if len(k) > 1]

    for item in catalog:
        item_name = item.get("name", "").lower()
        item_cat = item.get("category", "").lower()
        item_brand = item.get("brand", "").lower()
        item_price = item.get("price", 0)

        # 1. Price Check
        if max_price is not None and item_price > max_price:
            continue

        # 2. Brand Check
        if clean_brand and clean_brand not in item_brand:
            continue

        # 3. Category Check
        if clean_category and clean_category not in item_cat:
            continue

        # 4. Keyword / Query Match
        if keywords:
            # Check if any keyword matches name, category, or brand
            match = any(
                kw in item_name or kw in item_cat or kw in item_brand
                for kw in keywords
            )
            if not match:
                continue

        results.append(item)

    # Sort results by price ascending
    results.sort(key=lambda x: x.get("price", 0))
    return results

if __name__ == "__main__":
    print("\n--- Catalog Search Engine Test ---")
    
    test_1 = search_catalog(query="earbuds", max_price=2000)
    print(f"\nSearch: query='earbuds', max_price=2000 ({len(test_1)} found)")
    for p in test_1:
        print(f" - [{p['id']}] {p['name']} - Rs {p['price']}")

    test_2 = search_catalog(query="headphones", brand="Sony")
    print(f"\nSearch: query='headphones', brand='Sony' ({len(test_2)} found)")
    for p in test_2:
        print(f" - [{p['id']}] {p['name']} - Rs {p['price']}")

    print("\n----------------------------------")
