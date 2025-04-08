"""
Trend Analyzer and Style Recommendation Agent for AVA Style Assistant
Handles generating personalized style recommendations based on the user's analysis results
Uses Gemini AI to generate style advice and product recommendations
"""
from uagents import Agent, Context, Protocol
from uagents.setup import fund_agent_if_low
import os
import sys
from datetime import datetime
import json
import google.generativeai as genai
from dotenv import load_dotenv
import random
import urllib.parse
import re # Import regex module for parsing

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import message models
from models.message_models import (
    StyleRecommendationRequest,
    StyleRecommendationResponse
)

from utils.helpers import logger

# Load environment variables
load_dotenv()

# Configure Gemini API
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    logger.info("Gemini API configured successfully")
else:
    logger.warning("GOOGLE_API_KEY not set. Using fallback recommendations.")

# Use Gemini model
MODEL_NAME = "gemini-pro"

# Define recommendation agent with secure seed
RECOMMENDATION_AGENT_SEED = "recommendation_agent_secret_seed_phrase_32_bytes"
recommendation_agent = Agent(
    name="trend_analyzer",
    seed=RECOMMENDATION_AGENT_SEED,
    port=8002,
    endpoint=["http://localhost:8002/submit"],
)

# Fund the agent if balance is low
fund_agent_if_low(recommendation_agent.wallet.address())

# Create protocol for style recommendations
style_protocol = Protocol("StyleRecommendations")

def get_gemini_style_advice(body_type, face_shape, color_season):
    """Generate style advice and specific product recommendations using Gemini AI"""
    if not GOOGLE_API_KEY:
        logger.warning("Gemini API key not configured. Returning only fallback advice.")
        return get_fallback_recommendations(body_type, face_shape, color_season)
    
    try:
        # Updated prompt focusing on Indian retailers and INR prices
        prompt = f"""
        Act as an Indian fashion trend analyst and stylist. Based on the following user profile:
        - Body Type: {body_type}
        - Color Season: {color_season}
        {f'- Face Shape: {face_shape}' if face_shape != 'unknown' else ''}

        Generate personalized style recommendations that are SPECIFICALLY tailored to this user's body type, face shape, and color season.
        DO NOT use generic recommendations. Each suggestion must be based on the user's specific characteristics.

        Search for and describe 3-5 *specific, currently trending* clothing items available on Indian e-commerce platforms (Myntra, Ajio, Nykaa Fashion).
        For each item, provide the following details clearly:
        1. `Trending Item`: A specific, descriptive name that matches actual products (e.g., "H&M High-Waisted Wide-Leg Pants", "ONLY Oversized Blazer", "Zara Floral Print Midi Dress").
        2. `Brand`: Specify the brand name available in India (e.g., "H&M", "ONLY", "Zara", "W", "AND", "Global Desi")
        3. `Features`: Key features like cut, fabric, color, pattern
        4. `Suitability`: Explain SPECIFICALLY why this item suits the user's {body_type} body type and {color_season} color season
        5. `Styling`: Brief suggestions on how to wear it
        6. `Estimated Price INR`: Price range in Indian Rupees (e.g., "₹1,499 - ₹2,999")
        7. `Suggested Retailer`: One of: Myntra, Ajio, or Nykaa Fashion
        8. `Category`: The primary clothing category (e.g., 'pants', 'dresses', 'tops', 'outerwear', 'outfits')

        Present each item in this format:

        **Trending Item:** [Brand Name + Item Style]
        **Brand:** [Brand Name]
        **Features:** [Description]
        **Suitability:** [Explanation]
        **Styling:** [How to wear]
        **Estimated Price INR:** [Price in ₹]
        **Suggested Retailer:** [Indian Retailer]
        **Category:** [Category]

        IMPORTANT:
        1. All prices MUST be in Indian Rupees (₹)
        2. Only suggest items available on Myntra, Ajio, or Nykaa Fashion
        3. Each recommendation MUST be personalized based on the user's specific body type, face shape, and color season
        4. DO NOT use generic recommendations that could apply to anyone
        """
        
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        raw_advice = response.text
        logger.debug(f"Raw Gemini Response:\n{raw_advice}")

        # --- Parse Gemini Response for Products --- 
        recommendations = []
        item_blocks = re.split(r'\n(?= *\*\*Trending Item:\*\*)', raw_advice.strip())
        
        for block in item_blocks:
            if not block.strip():
                continue
                
            product = {
                "name": "Unknown Item",
                "brand": "",
                "description": "",
                "price": "₹ TBD",
                "retailer": "Online",
                "link": "#",
                "imageUrl": "/public/images/placeholder.png",
                "category": "unknown"
            }
            details_text = []

            # Extract details using regex for each field
            name_match = re.search(r'\*\*Trending Item:\*\*\s*(.*)', block)
            brand_match = re.search(r'\*\*Brand:\*\*\s*(.*)', block)
            features_match = re.search(r'\*\*Features:\*\*\s*(.*)', block)
            suitability_match = re.search(r'\*\*Suitability:\*\*\s*(.*)', block)
            styling_match = re.search(r'\*\*Styling:\*\*\s*(.*)', block)
            price_match = re.search(r'\*\*Estimated Price INR:\*\*\s*(.*)', block)
            retailer_match = re.search(r'\*\*Suggested Retailer:\*\*\s*(.*)', block)
            category_match = re.search(r'\*\*Category:\*\*\s*(.*)', block)

            if name_match: product["name"] = name_match.group(1).strip()
            if brand_match: product["brand"] = brand_match.group(1).strip()
            if features_match: details_text.append(f"Features: {features_match.group(1).strip()}")
            if suitability_match: details_text.append(f"Suitability: {suitability_match.group(1).strip()}")
            if styling_match: details_text.append(f"Styling: {styling_match.group(1).strip()}")
            if price_match: product["price"] = price_match.group(1).strip()
            if retailer_match: product["retailer"] = retailer_match.group(1).strip()
            if category_match: product["category"] = category_match.group(1).strip().lower()

            product["description"] = " \n ".join(details_text)
            
            # Generate more specific search links based on brand and item name
            search_term = f"{product['brand']} {product['name']}"
            encoded_search_term = urllib.parse.quote_plus(search_term)
            retailer_lower = product["retailer"].lower()

            if "myntra" in retailer_lower:
                # More specific Myntra search with brand filter
                brand_encoded = urllib.parse.quote_plus(product["brand"])
                product["link"] = f"https://www.myntra.com/{encoded_search_term}?f=Brand%3A{brand_encoded}"
            elif "ajio" in retailer_lower:
                # More specific AJIO search with brand filter
                product["link"] = f"https://www.ajio.com/search/?text={encoded_search_term}&brands={product['brand']}"
            elif "nykaa" in retailer_lower:
                # Nykaa Fashion search
                product["link"] = f"https://www.nykaafashion.com/search?q={encoded_search_term}&searchType=Manual"
            else:
                # Default to Myntra with specific search
                product["link"] = f"https://www.myntra.com/{encoded_search_term}"
                product["retailer"] = "Myntra"
                
            recommendations.append(product)

        style_advice_text = f"Based on your {body_type} body type and {color_season} color season, here are some trending items from popular Indian fashion retailers."

        if not recommendations:
             logger.warning("Could not parse any specific items from Gemini response. Returning fallback.")
             return get_fallback_recommendations(body_type, face_shape, color_season)

        return {
            "style_advice": style_advice_text,
            "recommendations": recommendations[:7]
        }
    
    except Exception as e:
        logger.error(f"Error in get_gemini_style_advice: {str(e)}", exc_info=True)
        return get_fallback_recommendations(body_type, face_shape, color_season)

def get_fallback_recommendations(body_type, face_shape, color_season):
    """Get fallback GENERAL style advice when Gemini API fails. No products included."""
    logger.warning("Executing fallback recommendation function.")
    
    # More detailed and personalized body type advice
    body_type_advice = {
        "hourglass": f"As someone with an hourglass figure (defined waist, balanced shoulders and hips), focus on pieces that highlight your natural curves. Look for wrap dresses, belted jackets, and high-waisted pants that emphasize your waist. Avoid boxy or shapeless clothing that hides your figure.",
        "pear": f"With your pear-shaped body (narrower shoulders, wider hips), create balance by drawing attention upward. Look for tops with interesting necklines, statement sleeves, and bright colors. For bottoms, choose A-line skirts and wide-leg pants that skim your hips. Avoid tight-fitting bottoms that emphasize your lower body.",
        "apple": f"For your apple-shaped body (broader shoulders, fuller midsection), create a defined waistline with strategic styling. Choose V-necks, empire waistlines, and structured jackets. Look for tops that skim rather than cling to your midsection. Avoid tight-fitting tops or high-waisted pants that emphasize your middle.",
        "rectangle": f"With your rectangular body shape (balanced shoulders and hips, less defined waist), create the illusion of curves. Look for peplum tops, full skirts, and belted pieces that create waist definition. Choose structured pieces that add shape. Avoid shapeless or overly loose clothing.",
        "inverted_triangle": f"For your inverted triangle shape (broader shoulders, narrower hips), balance your proportions by adding volume to your lower half. Look for full skirts, wide-leg pants, and detailed pockets. Choose tops that minimize shoulder width. Avoid shoulder pads or wide necklines that emphasize your upper body."
    }
    
    # More detailed and personalized face shape advice
    face_shape_advice = {
        "oval": f"With your oval face shape (balanced proportions, slightly curved jawline), you have the most versatile options. Experiment with different necklines, but avoid anything that makes your face appear too long. Look for collars and necklines that create width.",
        "round": f"For your round face shape (equal width and length, soft angles), create length and angles. Choose V-necks, rectangular necklines, and long earrings. Look for vertical details and avoid round necklines or circular patterns that emphasize roundness.",
        "square": f"With your square face shape (strong jawline, equal width and length), soften angles with rounded necklines and oval-shaped accessories. Look for collars that create curves and avoid sharp angles or square necklines that emphasize your angular features.",
        "heart": f"For your heart-shaped face (wider forehead, narrower chin), balance your proportions. Look for wider hems or pants and round or scoop necklines that complement your face. Avoid high necklines or narrow hems that emphasize your wider forehead.",
        "diamond": f"With your diamond face shape (narrow forehead and jaw, wider cheekbones), highlight your cheekbones. Look for boat necks and collared shirts that create width at the jawline. Avoid narrow necklines or styles that emphasize your narrow forehead."
    }
    
    # More detailed and personalized color season advice
    color_season_advice = {
        "winter": f"As a Winter color season (clear, bright colors with blue undertones), you look best in jewel tones like emerald, sapphire, and ruby. Choose pure white over cream, and opt for true black. Look for clear, bright colors rather than muted tones.",
        "summer": f"For your Summer color season (soft, muted colors with blue undertones), opt for gentle, cool tones. Look for lavender, powder blue, and soft rose. Choose silver over gold, and avoid bright or warm colors that might overwhelm your delicate coloring.",
        "autumn": f"With your Autumn color season (warm, muted earth tones), enhance your natural warmth. Look for olive green, terracotta, and golden yellow. Choose gold over silver, and avoid cool or bright colors that might clash with your warm undertones.",
        "spring": f"As a Spring color season (clear, warm colors), you look beautiful in coral, peach, and bright golden yellow. Choose warm, clear colors over muted or cool tones. Look for colors that reflect warmth and brightness."
    }
    
    body_advice = body_type_advice.get(body_type, "Focus on pieces that make you feel comfortable and confident.")
    face_advice = face_shape_advice.get(face_shape, "Choose necklines and accessories that frame your face in a way that feels flattering.")
    color_advice = color_season_advice.get(color_season, "Choose colors that make you feel confident. Neutrals like navy, black, and white work for everyone.")
    
    style_advice = f"**Personalized Style Advice:**\n\n{body_advice}\n\n{face_advice}\n\n{color_advice}"
    
    return {
        "style_advice": style_advice,
        "recommendations": [] # No products in fallback
    }

# Style recommendation handler (adjust response structure if needed)
@style_protocol.on_message(model=StyleRecommendationRequest, replies={StyleRecommendationResponse})
async def handle_style_recommendation(ctx: Context, sender: str, msg: StyleRecommendationRequest):
    """Handle style recommendation requests using Gemini for products"""
    ctx.logger.info(f"Received style recommendation request from {sender} for profile: {msg.dict()}")
    
    try:
        body_type = msg.body_type
        face_shape = msg.face_shape
        color_season = msg.color_season
        
        # Get advice and product recommendations directly from Gemini
        style_result = get_gemini_style_advice(body_type, face_shape, color_season)
        
        # The response structure needs adjustment based on how the frontend uses it.
        # The frontend's displayTrendRecommendations expects styleAdvice and recommendations list.
        # Let's keep the response simple for now.
        
        response = StyleRecommendationResponse(
            # Keep the 'recommendations' key, but now it holds the list of products directly
            recommendations={"products": style_result.get("recommendations", [])}, 
            success=True,
            # Add style advice here if needed separately, or let frontend parse it?
            # For now, let's assume frontend primarily uses the product list.
            # We might need to adjust the frontend JS later if it relied on the categorized advice.
            error=None # Ensure error is None on success
        )
        # Manually adding style advice to the response dictionary sent back
        # This structure might need tweaking based on exact frontend needs
        response_dict = response.dict()
        response_dict['style_advice'] = style_result.get('style_advice', 'No specific advice generated.')

        # Sending the modified dictionary
        # NOTE: This bypasses the strict model validation of StyleRecommendationResponse 
        #       if 'style_advice' isn't part of its definition. 
        #       A cleaner way might be to add style_advice to the Model itself.
        #       However, sending a dict often works if the receiver handles it flexibly.
        await ctx.send(sender, response_dict)

        ctx.logger.info(f"Style recommendations complete.")
        
    except Exception as e:
        ctx.logger.error(f"Error processing style recommendation: {str(e)}", exc_info=True)
        # Send a structured error response
        error_response_model = StyleRecommendationResponse(
            recommendations={},
            success=False,
            error=f"Recommendation failed: {str(e)}"
        )
        await ctx.send(sender, error_response_model)

# Register protocol with the agent
recommendation_agent.include(style_protocol)

if __name__ == "__main__":
    logger.info(f"Starting recommendation agent with address: {recommendation_agent.address}")
    recommendation_agent.run() 