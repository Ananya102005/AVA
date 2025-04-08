from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import logging
import google.generativeai as genai
import sys
from datetime import datetime
import re
import urllib.parse
from dotenv import load_dotenv # Import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("trend_server")

# Configure Gemini API with your API key
# Get the key from environment ONLY, remove hardcoded fallback
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY") 
if not GOOGLE_API_KEY:
    logger.critical("GOOGLE_API_KEY not found in environment variables. Please set it in the .env file.")
    # Optionally exit or handle the absence of the key appropriately
    # sys.exit("API Key not configured.") 
    # For now, let it proceed but Gemini calls will fail
else:
    genai.configure(api_key=GOOGLE_API_KEY)

# Use Gemini model
MODEL_NAME = "models/gemini-1.5-flash"

# Sample retailers with base URLs
RETAILERS = {
    "Myntra": "https://www.myntra.com/search?q=",
    "Amazon": "https://www.amazon.in/s?k=",
    "Nykaa Fashion": "https://www.nykaafashion.com/search/?text=",
    "Ajio": "https://www.ajio.com/search/?text="
}

# Update the DEFAULT_IMAGES with direct image URLs that are more reliable
DEFAULT_IMAGES = {
    "tops": "https://m.media-amazon.com/images/I/71eTwm2lHYL._SY679_.jpg",
    "dresses": "https://m.media-amazon.com/images/I/61O85yC1lFL._SY741_.jpg",
    "jeans": "https://m.media-amazon.com/images/I/71Q-Hp6rCbL._SY741_.jpg",
    "skirts": "https://m.media-amazon.com/images/I/61qmeYBtfxL._SY741_.jpg",
    "bottoms": "https://m.media-amazon.com/images/I/71pyhMgV6tL._SY741_.jpg",
    "formal": "https://m.media-amazon.com/images/I/71qd1G4chwL._SY741_.jpg",
    "casual": "https://m.media-amazon.com/images/I/81KGraqiN3L._SY741_.jpg",
    "party": "https://m.media-amazon.com/images/I/71Oy38X2GEL._SY741_.jpg",
    "beach": "https://m.media-amazon.com/images/I/81yLbbvZKUL._SY741_.jpg",
    "outerwear": "https://m.media-amazon.com/images/I/71f9TcjZyQL._SY741_.jpg"
}

# Additional backup images for specific item types
ITEM_TYPE_IMAGES = {
    "velvet dress": "https://m.media-amazon.com/images/I/61J7rBXQgDL._SL1280_.jpg",
    "midi dress": "https://m.media-amazon.com/images/I/71Oy38X2GEL._SY741_.jpg",
    "flutter sleeve": "https://m.media-amazon.com/images/I/71Oy38X2GEL._SY741_.jpg",
    "wide leg": "https://m.media-amazon.com/images/I/61-eTthXiYL._SY741_.jpg",
    "palazzo": "https://m.media-amazon.com/images/I/61-eTthXiYL._SY741_.jpg",
    "asymmetrical": "https://m.media-amazon.com/images/I/71JsEmdKEwL._SY741_.jpg",
    "jumpsuit": "https://m.media-amazon.com/images/I/81Ql4lOH28L._SY741_.jpg",
    "satin cami": "https://m.media-amazon.com/images/I/61-MtlGITZL._SY741_.jpg",
    "sequin": "https://m.media-amazon.com/images/I/91bKnFeTQ0L._SY741_.jpg",
    "wrap top": "https://m.media-amazon.com/images/I/71eTwm2lHYL._SY679_.jpg",
    "bootcut": "https://m.media-amazon.com/images/I/71ZP5XRbFuL._SY741_.jpg",
    "turtleneck": "https://m.media-amazon.com/images/I/71mNOmCVR6L._SY741_.jpg",
    "a-line velvet": "https://rukminim2.flixcart.com/image/550/650/xif0q/dress/j/d/f/m-dr1042-purvaja-original-imagr5uzbgauu6zg.jpeg",
    "high-waisted wide-leg": "https://rukminim2.flixcart.com/image/550/650/xif0q/trouser/y/i/d/28-cd1094-cottondaraacollections-original-imagrysbm2fz8dyg.jpeg",
    "sequin embellished": "https://rukminim2.flixcart.com/image/550/650/kxnl6kw0/top/y/a/k/m-tttp005969-tokyo-talkies-original-imaga25u6kngfpbg.jpeg",
    "ruffle detail": "https://rukminim2.flixcart.com/image/550/650/xif0q/skirt/k/5/l/s-sk2152-purplicious-original-imagnefz3ybz9pgz.jpeg",
    "one-shoulder jumpsuit": "https://rukminim2.flixcart.com/image/550/650/xif0q/jumpsuit/t/3/c/m-kf4032-vritika-original-imagkq3znvpfmhsf-bb.jpeg",
    "dark wash bootcut": "https://rukminim2.flixcart.com/image/550/650/xif0q/jean/r/q/i/28-21325-0456-levi-s-original-imagq6nshf8vknnt-bb.jpeg",
    "floral": "https://m.media-amazon.com/images/I/81LITmbKAlL._SY741_.jpg",
    "floral print": "https://m.media-amazon.com/images/I/81LITmbKAlL._SY741_.jpg",
    "striped": "https://m.media-amazon.com/images/I/71+y8kx8YQL._SY741_.jpg",
    "stripe": "https://m.media-amazon.com/images/I/71+y8kx8YQL._SY741_.jpg",
    "maxi dress": "https://m.media-amazon.com/images/I/61pVw77fA0L._SY741_.jpg",
    "maxi skirt": "https://m.media-amazon.com/images/I/71P--o+pXFL._SY741_.jpg",
    "mini skirt": "https://m.media-amazon.com/images/I/61X5nOMtVaL._SY741_.jpg",
    "puffer jacket": "https://m.media-amazon.com/images/I/61fSCfTkGSL._SY741_.jpg",
    "blazer": "https://m.media-amazon.com/images/I/61sDMkA7DUL._SY741_.jpg",
    "cardigan": "https://m.media-amazon.com/images/I/81gY0lJgxPL._SY741_.jpg",
    "linen": "https://m.media-amazon.com/images/I/71n57zQJ10L._SY741_.jpg",
    "silk": "https://m.media-amazon.com/images/I/61yAPGu7uML._SY679_.jpg",
    "lace": "https://m.media-amazon.com/images/I/816J9rrsREL._SY741_.jpg",
    "denim jacket": "https://m.media-amazon.com/images/I/81a2TQrptxL._SY741_.jpg",
    "leather jacket": "https://m.media-amazon.com/images/I/61sWPd1oQDL._SY741_.jpg",
    "embroidered": "https://m.media-amazon.com/images/I/81G8dQg+AIL._SY741_.jpg",
    "puff sleeve": "https://m.media-amazon.com/images/I/61Nqolq4LWL._SY679_.jpg",
    "v-neck": "https://m.media-amazon.com/images/I/71lK3rzpG9L._SY741_.jpg",
    "bodycon": "https://m.media-amazon.com/images/I/61JgQmqj4cL._SY741_.jpg",
    "cargo pants": "https://m.media-amazon.com/images/I/61mVXmM0WtL._SY741_.jpg"
}

def get_enhanced_search_query(base_query, user_profile):
    """
    Enhance a basic search query using the user's body profile
    """
    body_type = user_profile.get("bodyType", "").lower()
    face_shape = user_profile.get("faceShape", "").lower()
    color_season = user_profile.get("colorSeason", "").lower()
    
    enhanced_query = f"women's {base_query}"
    
    # Add body type if available
    if body_type:
        if body_type == "invertedtriangle":
            enhanced_query += " for inverted triangle body shape"
        elif body_type:
            enhanced_query += f" for {body_type} body shape"
    
    # Add color season if available
    if color_season:
        enhanced_query += f" {color_season} colors"
    
    return enhanced_query

def get_trending_items(body_profile):
    """Get trending items, trying Gemini API first, then fallback."""
    # Ensure API key is configured before proceeding
    if not GOOGLE_API_KEY:
        logger.error("Cannot call Gemini API: GOOGLE_API_KEY is not configured.")
        return get_body_type_specific_items(body_profile.get("bodyType", "unknown"), body_profile.get("category", None))

    body_type = body_profile.get("bodyType", "unknown").lower()
    face_shape = body_profile.get("faceShape", "unknown").lower()
    color_season = body_profile.get("colorSeason", "unknown").lower()
    category = body_profile.get("category", None) # Get category if provided

    logger.info(f"Attempting to get trending items from Gemini API for profile: Body={body_type}, Face={face_shape}, Color={color_season}, Category={category}")
    try:
        # Construct a more detailed prompt asking for specific keywords
        prompt = f"""
        Generate a list of 6 currently trending women's fashion items suitable for a person with:
        - Body Type: {body_type}
        - Face Shape: {face_shape}
        - Color Season: {color_season}
        {f'- Category: {category}' if category else '- Across various categories'}
        
        For each item, provide:
        1. `name`: A descriptive name including key style elements (e.g., 'A-Line Velvet Midi Dress', 'High-Waisted Wide-Leg Linen Trousers'). Include specific keywords like 'floral', 'striped', 'sequin', 'velvet', 'linen', 'silk', 'cotton', 'wool', 'wide-leg', 'bootcut', 'flare', 'pencil', 'midi', 'maxi', 'mini', 'puff-sleeve', 'v-neck', 'turtleneck'.
        2. `description`: A short explanation of why it's suitable and trendy.
        3. `price`: An estimated price range in INR (e.g., '₹1500-₹3000').
        4. `category`: The most relevant category (e.g., 'dresses', 'tops', 'jeans', 'skirts', 'outerwear', 'bottoms', 'accessories', 'footwear').
        5. `retailer`: Suggest one popular Indian online retailer (Myntra, Amazon, Ajio, Nykaa Fashion).
        
        Format the output as a JSON list of objects. Example format:
        [
            {{ "name": "Example Name with Keywords", "description": "Why it works", "price": "₹1000-₹2000", "category": "example_category", "retailer": "Myntra" }},
            ...
        ]
        Ensure the JSON is valid. Only provide the JSON list, no other text before or after.
        """

        # Call Gemini for trending items
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        
        # Log the raw response text for debugging
        logger.debug(f"Raw Gemini Response Text: {response.text}")
        
        # Clean the response text (handle potential markdown code blocks)
        cleaned_response_text = response.text.strip()
        if cleaned_response_text.startswith('```json'):
            cleaned_response_text = cleaned_response_text[7:]
        if cleaned_response_text.startswith('```'):
             cleaned_response_text = cleaned_response_text[3:]
        if cleaned_response_text.endswith('```'):
            cleaned_response_text = cleaned_response_text[:-3]
        cleaned_response_text = cleaned_response_text.strip()

        logger.debug(f"Cleaned Gemini Response for JSON parsing: {cleaned_response_text}")
        
        try:
            trending_items = json.loads(cleaned_response_text)
            logger.info(f"Successfully parsed trending items from Gemini: {len(trending_items)} items")
            
            # Process items: Add image URLs and product URLs
            processed_items = []
            for item in trending_items:
                name = item.get("name", "")
                item_category = item.get("category", "").lower()
                retailer = item.get("retailer", "Myntra") # Default to Myntra if not provided
                
                # Refined search term generation
                search_term_keywords = name.replace("-", " ").replace("(", "").replace(")", "").replace("&", " and ") # Clean up name for search
                search_term = f"{search_term_keywords} women {item_category}"
                encoded_search_term = urllib.parse.quote_plus(search_term)
                
                # Generate retailer-specific search URLs
                if retailer == "Myntra":
                    item["productUrl"] = f"https://www.myntra.com/{encoded_search_term}?rawQuery={encoded_search_term}" # Use rawQuery for better matching
                elif retailer == "Amazon":
                    item["productUrl"] = f"https://www.amazon.in/s?k={encoded_search_term}"
                elif retailer == "Nykaa Fashion":
                    item["productUrl"] = f"https://www.nykaafashion.com/search?q={encoded_search_term}"
                elif retailer == "Ajio":
                    item["productUrl"] = f"https://www.ajio.com/search/?text={encoded_search_term}"
                else: # Fallback to Google Shopping
                    item["productUrl"] = f"https://www.google.com/search?q={encoded_search_term}&tbm=shop"
                
                item["imageUrl"] = get_product_image_url(name, item_category)
                item["trending"] = True # Mark as trending
                processed_items.append(item)
            
            return processed_items[:6] # Return max 6 items
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response from Gemini: {e}")
            logger.error(f"Invalid JSON string received: {cleaned_response_text}")
            # Fall through to fallback mechanism
            logger.warning("Falling back to static trending items due to JSON parsing error.")
            return get_body_type_specific_items(body_type, category)
        except Exception as e:
            # Catch other potential errors during processing
            logger.error(f"Error processing Gemini response: {e}", exc_info=True)
            logger.warning("Falling back to static trending items due to processing error.")
            return get_body_type_specific_items(body_type, category)

    except Exception as e:
        logger.error(f"Error calling Gemini API for trending items: {e}", exc_info=True)
        # Fall through to fallback mechanism
        logger.warning("Falling back to static trending items due to Gemini API call error.")
        return get_body_type_specific_items(body_type, category)

    # --- Fallback Mechanism (should only be reached if Gemini fails) ---
    # logger.warning("Falling back to static trending items.") # This log is now within the catch blocks
    # return get_body_type_specific_items(body_type, category) # This return is now within the catch blocks

def get_body_type_specific_items(body_type, category=None):
    """Generate fallback items based on body type and category."""
    logger.warning(f"Executing FALLBACK for body type: {body_type}, category: {category}")
    # Return a clear message instead of static items
    fallback_message = {
        "name": "Fallback Activated",
        "description": "Could not retrieve dynamic trends from Gemini API. Showing this fallback message instead. Please check Trend Server logs for errors.",
        "price": "N/A",
        "retailer": "System",
        "category": "Error",
        "productUrl": "#",
        "imageUrl": "/public/images/error.png", # Consider adding an error image
        "trending": False
    }
    return [fallback_message] # Return as a list containing the single message object

def extract_items_from_text(text):
    """Extract structured item data from text when JSON parsing fails"""
    items = []
    # Simple regex-based extraction
    product_sections = re.split(r'\d+\.\s+', text)[1:]  # Split by numbered items
    
    for i, section in enumerate(product_sections):
        if not section.strip():
            continue
            
        # Extract the name (first line typically)
        name_match = re.search(r'^([^:]+?)(?:\n|:)', section)
        name = name_match.group(1).strip() if name_match else f"Trending Item {i+1}"
        
        # Extract description
        desc_match = re.search(r'Description:?\s*([^\n]+)', section, re.IGNORECASE) or \
                    re.search(r'Why:?\s*([^\n]+)', section, re.IGNORECASE)
        description = desc_match.group(1).strip() if desc_match else "Trending fashion item"
        
        # Extract price
        price_match = re.search(r'Price:?\s*([^\n]+)', section, re.IGNORECASE) or \
                    re.search(r'\$\s*([^\n]+)', section)
        price = price_match.group(1).strip() if price_match else "$49.99 - $99.99"
        if not price.startswith('$'):
            price = f"${price}"
            
        # Extract retailer
        retailer_match = re.search(r'Retailer:?\s*([^\n]+)', section, re.IGNORECASE)
        retailer = retailer_match.group(1).strip() if retailer_match else "Myntra"
        
        # Extract or guess category
        category_match = re.search(r'Category:?\s*([^\n]+)', section, re.IGNORECASE)
        name_lower = name.lower()
        if category_match:
            category = category_match.group(1).strip().lower()
        elif any(word in name_lower for word in ["dress", "gown", "frock"]):
            category = "dresses"
        elif any(word in name_lower for word in ["jeans", "pant", "trouser"]):
            category = "jeans"
        elif any(word in name_lower for word in ["top", "blouse", "shirt"]):
            category = "tops"
        elif any(word in name_lower for word in ["skirt"]):
            category = "skirts"
        else:
            category = "casual"
        
        # Create search URL
        search_term = name.replace(" ", "+")
        productUrl = f"{RETAILERS.get(retailer, RETAILERS['Myntra'])}{search_term}"
        
        items.append({
            "name": name,
            "description": description,
            "price": price,
            "retailer": retailer,
            "category": category,
            "productUrl": productUrl,
            "imageUrl": DEFAULT_IMAGES.get(category, DEFAULT_IMAGES["casual"]),
            "trending": True
        })
    
    return items if items else get_fallback_trending_items(None)

def search_products(query, user_profile):
    """Search products using Gemini API first, then fallback."""
    body_type = user_profile.get("bodyType", "unknown").lower()
    face_shape = user_profile.get("faceShape", "unknown").lower()
    color_season = user_profile.get("colorSeason", "unknown").lower()
    
    logger.info(f"Attempting to search products via Gemini API for term: '{query}' and profile: Body={body_type}, Face={face_shape}, Color={color_season}")
    try:
        # Refined prompt for search
        prompt = f"""
        Find 6 specific women's fashion products matching the search term '{query}'.
        Tailor the results for a person with:
        - Body Type: {body_type}
        - Face Shape: {face_shape}
        - Color Season: {color_season}
        
        For each product, provide:
        1. `name`: A specific product name including descriptive keywords (e.g., 'Levi's 501 Original Fit Jeans', 'Zara Floral Print Midi Skirt'). Include keywords like material (cotton, silk), fit (slim, regular, wide), style (boho, formal), and features (pleated, embroidered).
        2. `description`: A brief description highlighting suitability for the profile.
        3. `price`: An estimated price range in INR.
        4. `category`: The product category.
        5. `retailer`: Suggest one popular Indian online retailer (Myntra, Amazon, Ajio, Nykaa Fashion).
        
        Format as a JSON list of objects. Example:
        [
            { "name": "Specific Brand Product Name with Keywords", "description": "Why it fits the profile", "price": "₹2000-₹4000", "category": "jeans", "retailer": "Amazon" },
            ...
        ]
        Only provide the JSON list.
        """

        # Call Gemini for search results
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        
        # Clean the response text
        cleaned_response_text = response.text.strip().lstrip('```json').lstrip('```').rstrip('```')
        logger.debug(f"Cleaned Gemini Search Response: {cleaned_response_text}")
        
        try:
            search_results = json.loads(cleaned_response_text)
            logger.info(f"Successfully parsed search results from Gemini: {len(search_results)} items")
            
            # Process items: Add image URLs and product URLs
            processed_items = []
            for item in search_results:
                name = item.get("name", "")
                item_category = item.get("category", "").lower()
                retailer = item.get("retailer", "Myntra")
                
                # Refined search term generation
                search_term_keywords = name.replace("-", " ").replace("(", "").replace(")", "").replace("&", " and ")
                search_query = f"{search_term_keywords} women {item_category}"
                encoded_search_query = urllib.parse.quote_plus(search_query)
                
                # Generate retailer-specific search URLs
                if retailer == "Myntra":
                    item["productUrl"] = f"https://www.myntra.com/{encoded_search_query}?rawQuery={encoded_search_query}"
                elif retailer == "Amazon":
                    item["productUrl"] = f"https://www.amazon.in/s?k={encoded_search_query}"
                elif retailer == "Nykaa Fashion":
                    item["productUrl"] = f"https://www.nykaafashion.com/search?q={encoded_search_query}"
                elif retailer == "Ajio":
                    item["productUrl"] = f"https://www.ajio.com/search/?text={encoded_search_query}"
                else:
                    item["productUrl"] = f"https://www.google.com/search?q={encoded_search_query}&tbm=shop"
                
                item["imageUrl"] = get_product_image_url(name, item_category)
                processed_items.append(item)
            
            return processed_items[:6]
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response from Gemini search: {e}")
            logger.error(f"Invalid JSON string from search: {cleaned_response_text}")
            # Fall through to fallback mechanism

    except Exception as e:
        logger.error(f"Error calling Gemini API for search: {e}", exc_info=True)
        # Fall through to fallback mechanism

    # --- Fallback Mechanism ---
    logger.warning(f"Falling back to static search results for term: '{query}'.")
    return get_search_specific_items(query) # Use simpler fallback for search

def get_search_specific_items(search_term):
    """Generate very basic fallback search items."""
    # Simple fallback: return a few generic items related to the search term category if possible
    # Or just return generic trending items as a last resort.
    # This part could be enhanced, but for now, let's keep it minimal.
    
    logger.info(f"Generating static fallback for search term: {search_term}")
    # Try to guess a category from the search term for basic filtering
    guessed_category = None
    term_lower = search_term.lower()
    if "dress" in term_lower:
        guessed_category = "dresses"
    elif "top" in term_lower or "blouse" in term_lower or "shirt" in term_lower:
        guessed_category = "tops"
    elif "jean" in term_lower or "trouser" in term_lower or "pant" in term_lower:
        guessed_category = "bottoms" # Or jeans specifically?
    elif "skirt" in term_lower:
        guessed_category = "skirts"
    elif "coat" in term_lower or "jacket" in term_lower:
        guessed_category = "outerwear"
    
    # Use the general items from the body type function
    items = get_body_type_specific_items("unknown", guessed_category) # Get generic items, potentially filtered
    
    # Process these items to ensure they have URLs and images
    processed_fallback_items = []
    for item in items[:3]: # Return fewer items for fallback search
        name = item.get("name", "")
        item_category = item.get("category", "").lower()
        retailer = item.get("retailer", "Myntra")
        
        # Use the original search term for the fallback URL if it's more specific
        search_query = f"{search_term} {name} women {item_category}"
        encoded_search_query = urllib.parse.quote_plus(search_query)
        
        # Generate retailer-specific search URLs (mirrored logic)
        if retailer == "Myntra":
            item["productUrl"] = f"https://www.myntra.com/{encoded_search_query}?rawQuery={encoded_search_query}"
        elif retailer == "Amazon":
            item["productUrl"] = f"https://www.amazon.in/s?k={encoded_search_query}"
        elif retailer == "Nykaa Fashion":
            item["productUrl"] = f"https://www.nykaafashion.com/search?q={encoded_search_query}"
        elif retailer == "Ajio":
            item["productUrl"] = f"https://www.ajio.com/search/?text={encoded_search_query}"
        else:
            item["productUrl"] = f"https://www.google.com/search?q={encoded_search_query}&tbm=shop"
        
        item["imageUrl"] = get_product_image_url(name, item_category)
        processed_fallback_items.append(item)
    
    return processed_fallback_items

def get_test_data():
    """Generate realistic test data for the test endpoint"""
    return {
        "trending": [
            {
                "name": "Floral Print Maxi Dress",
                "description": "Elegant floral print maxi dress with a flattering silhouette, perfect for summer events",
                "price": "₹1,499",
                "retailer": "Myntra",
                "category": "dresses",
                "imageUrl": DEFAULT_IMAGES["dresses"],
                "productUrl": "https://www.myntra.com/search?q=Floral+Print+Maxi+Dress",
                "trending": True
            },
            {
                "name": "High-Waisted Wide Leg Pants",
                "description": "Sophisticated wide-leg pants that elongate your silhouette and provide all-day comfort",
                "price": "₹1,299",
                "retailer": "Amazon",
                "category": "bottoms",
                "imageUrl": DEFAULT_IMAGES["jeans"],
                "productUrl": "https://www.amazon.in/s?k=High-Waisted+Wide+Leg+Pants",
                "trending": True
            },
            {
                "name": "Oversized Linen Blazer",
                "description": "Trendy oversized linen blazer in a neutral tone that pairs well with any outfit",
                "price": "₹2,799",
                "retailer": "Nykaa Fashion",
                "category": "outerwear",
                "imageUrl": DEFAULT_IMAGES["formal"],
                "productUrl": "https://www.nykaafashion.com/search/?text=Oversized+Linen+Blazer",
                "trending": True
            },
            {
                "name": "Ribbed Knit Crop Top",
                "description": "Form-fitting ribbed knit crop top that's versatile for both casual and dressy looks",
                "price": "₹799",
                "retailer": "Ajio",
                "category": "tops",
                "imageUrl": DEFAULT_IMAGES["tops"],
                "productUrl": "https://www.ajio.com/search/?text=Ribbed+Knit+Crop+Top",
                "trending": True
            },
            {
                "name": "Pleated Midi Skirt",
                "description": "Elegant pleated midi skirt with flowing movement, ideal for office or evening wear",
                "price": "₹1,199",
                "retailer": "Myntra",
                "category": "skirts",
                "imageUrl": DEFAULT_IMAGES["skirts"],
                "productUrl": "https://www.myntra.com/search?q=Pleated+Midi+Skirt",
                "trending": True
            },
            {
                "name": "Statement Collar Blouse",
                "description": "Fashionable blouse with a statement collar that adds a modern touch to your wardrobe",
                "price": "₹899",
                "retailer": "Amazon",
                "category": "tops",
                "imageUrl": DEFAULT_IMAGES["tops"],
                "productUrl": "https://www.amazon.in/s?k=Statement+Collar+Blouse",
                "trending": True
            }
        ],
        "enhanced_query": "Sample enhanced query for your body type",
        "results": [
            {
                "name": "Wrap Front Dress",
                "description": "Flattering wrap dress that accentuates your curves and creates a balanced silhouette",
                "price": "₹1,599",
                "retailer": "Myntra",
                "category": "dresses",
                "imageUrl": DEFAULT_IMAGES["dresses"],
                "productUrl": "https://www.myntra.com/search?q=Wrap+Front+Dress"
            },
            {
                "name": "Straight Leg Jeans",
                "description": "Classic straight leg jeans that provide a timeless, balanced look for any occasion",
                "price": "₹1,299",
                "retailer": "Ajio",
                "category": "jeans",
                "imageUrl": DEFAULT_IMAGES["jeans"],
                "productUrl": "https://www.ajio.com/search/?text=Straight+Leg+Jeans"
            },
            {
                "name": "Puff Sleeve Blouse",
                "description": "Trendy puff sleeve blouse that adds volume to the upper body while maintaining elegance",
                "price": "₹899",
                "retailer": "Nykaa Fashion",
                "category": "tops",
                "imageUrl": DEFAULT_IMAGES["tops"],
                "productUrl": "https://www.nykaafashion.com/search/?text=Puff+Sleeve+Blouse"
            },
            {
                "name": "A-Line Midi Skirt",
                "description": "Versatile A-line midi skirt that flatters all body types with its balanced proportions",
                "price": "₹1,199",
                "retailer": "Amazon",
                "category": "skirts",
                "imageUrl": DEFAULT_IMAGES["skirts"],
                "productUrl": "https://www.amazon.in/s?k=A-Line+Midi+Skirt"
            },
            {
                "name": "Belted Shirt Dress",
                "description": "Sophisticated shirt dress with a belt that defines the waist and creates an hourglass effect",
                "price": "₹1,799",
                "retailer": "Myntra",
                "category": "dresses",
                "imageUrl": DEFAULT_IMAGES["dresses"],
                "productUrl": "https://www.myntra.com/search?q=Belted+Shirt+Dress"
            },
            {
                "name": "Cropped Wide Leg Pants",
                "description": "Fashionable cropped wide leg pants that create a balanced look and elongate the legs",
                "price": "₹1,499",
                "retailer": "Ajio",
                "category": "bottoms",
                "imageUrl": DEFAULT_IMAGES["jeans"],
                "productUrl": "https://www.ajio.com/search/?text=Cropped+Wide+Leg+Pants"
            }
        ]
    }

# Add a function to get the most appropriate image for a product
def get_product_image_url(product_name, category):
    """Get the most appropriate image URL for the product based on name and category"""
    name_lower = product_name.lower()
    
    # First check for specific item types in the name
    for keyword, url in ITEM_TYPE_IMAGES.items():
        if keyword in name_lower:
            return url
    
    # Fall back to category images
    if category and category.lower() in DEFAULT_IMAGES:
        return DEFAULT_IMAGES[category.lower()]
    
    # Final fallback
    return DEFAULT_IMAGES["casual"]

class TrendRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the trend analyzer server"""
    
    def _send_headers(self, status_code, content_type="application/json"):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        # Add CORS headers to allow requests from any origin
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def _send_response(self, status_code, data):
        self._send_headers(status_code)
        response = json.dumps(data).encode('utf-8')
        self.wfile.write(response)
    
    def do_OPTIONS(self):
        # Handle preflight requests for CORS
        self._send_headers(200)
    
    def do_GET(self):
        try:
            if self.path == "/health":
                # Health check endpoint
                self._send_response(200, {"status": "healthy", "timestamp": datetime.now().isoformat()})
            
            elif self.path == "/test":
                # Test endpoint with sample data
                self._send_response(200, get_test_data())
            
            else:
                logger.warning(f"Unknown endpoint requested: {self.path}")
                self._send_response(404, {"error": "Endpoint not found"})
        
        except Exception as e:
            logger.error(f"Error processing GET request: {str(e)}")
            self._send_response(500, {"error": str(e)})
    
    def do_POST(self):
        try:
            # Handle POST requests
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)

            if self.path == '/trending':
                profile = data.get('profile', {})
                category = data.get('category', None)
                # Add category to profile if provided
                if category:
                    profile['category'] = category 
                
                trending_items = get_trending_items(profile)
                # Log the data being sent back
                logger.debug(f"Sending trending response: {json.dumps({'trending': trending_items}, indent=2)}") 
                self._send_response(200, {"trending": trending_items})
                logger.info(f"Trending items request processed successfully, sent {len(trending_items)} items.")
            
            elif self.path == "/search":
                profile = data.get('profile', {})
                query = data.get('query', '')
                
                search_results = search_products(query, profile)
                response_data = {
                    "results": search_results,
                    "enhanced_query": get_enhanced_search_query(query, profile)
                }
                # Log the data being sent back
                logger.debug(f"Sending search response: {json.dumps(response_data, indent=2)}")
                self._send_response(200, response_data)
            
            else:
                self._send_response(404, {"error": "Not Found"})
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
            self._send_response(400, {"error": "Invalid JSON"})
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            self._send_response(500, {"error": str(e)})

if __name__ == "__main__":
    # Start HTTP server
    port = int(os.environ.get('TREND_PORT', 7000))
    try:
        server = HTTPServer(('', port), TrendRequestHandler)
        logger.info(f"Starting HTTP server on port {port}")
        
        # Print startup message
        print("\n=== Trend Analyzer & Stylist Server Starting ===")
        print(f"\nUsing Gemini model: {MODEL_NAME}")
        print(f"\nAPI Key configured: {bool(GOOGLE_API_KEY)}")
        print("\nAvailable endpoints:")
        print("- GET /health - Health check endpoint")
        print("- GET /test - Test endpoint with sample data")
        print("- POST /trending - Get trending items based on user profile")
        print("- POST /search - Search for items based on query and user profile")
        print(f"\nServer is running on http://localhost:{port}")
        
        # Start the server
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.server_close()
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        print(f"Error starting server: {e}")
        sys.exit(1) 