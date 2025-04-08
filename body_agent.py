"""
Body Analysis Agent for AVA Style Assistant
Handles body shape, face shape, and color season analysis
"""
from uagents import Agent, Context, Protocol, Model
from uagents.setup import fund_agent_if_low

import os
import json
import logging
import sys
from typing import Dict, Any, Union, List
import google.generativeai as genai
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import helper functions
from utils.helpers import (
    logger,
    determine_body_type, 
    determine_face_shape,
    determine_color_season,
    BODY_TYPES,
    FACE_SHAPES,
    COLOR_SEASONS
)

# Import message models
from models.message_models import (
    BodyAnalysisRequest,
    BodyAnalysisResponse,
    FaceAnalysisRequest,
    FaceAnalysisResponse,
    ColorAnalysisRequest,
    ColorAnalysisResponse,
    ErrorResponse,
    # New Gemini-enhanced models
    GeminiBodyAnalysisRequest,
    GeminiBodyAnalysisResponse,
    GeminiFaceAnalysisRequest,
    GeminiFaceAnalysisResponse,
    GeminiColorAnalysisRequest,
    GeminiColorAnalysisResponse
)

# Load environment variables
load_dotenv()

# Configure Gemini API
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    logger.info("Gemini API configured successfully for body agent")
else:
    logger.warning("GOOGLE_API_KEY not set. Using fallback analysis methods.")

# Use Gemini model
MODEL_NAME = "gemini-pro"

# Create the agent with a secure seed phrase
SEED_PHRASE = os.getenv("BODY_AGENT_SEED", "body analysis agent secure seed phrase")
body_agent = Agent(
    name="body-analyzer",
    seed=SEED_PHRASE,
    port=8001,
    endpoint=["http://127.0.0.1:8001/submit"],
)

# Fund the agent if balance is low
fund_agent_if_low(body_agent.wallet.address())

# Define protocol for body analysis
body_analysis_protocol = Protocol("BodyAnalysis", version="0.1.0")

# --- Gemini Helper Functions ---

def get_gemini_body_analysis(description: str, additional_context: str = None) -> Dict[str, Any]:
    """Get body analysis from Gemini AI."""
    if not GOOGLE_API_KEY:
        logger.warning("No API key found, falling back to basic analysis")
        return get_fallback_body_analysis(description)
    
    try:
        prompt = f"""
        You are a professional fashion stylist and body type analyst. Analyze the following body description and provide a detailed, personalized body type analysis.

        Description: {description}
        {f"Additional Context: {additional_context}" if additional_context else ""}

        Based on the description, determine the most accurate body type from these options:
        - Hourglass (balanced shoulders and hips with defined waist)
        - Pear/Triangle (narrower shoulders, wider hips)
        - Apple (fuller midsection, proportional shoulders and hips)
        - Rectangle (straight up and down, less defined waist)
        - Inverted Triangle (broader shoulders, narrower hips)

        Provide a detailed, personalized response in this JSON format:
        {{
            "body_type": "one of the above types",
            "detailed_analysis": "A personalized analysis that references specific details from their description",
            "style_recommendations": [
                "5 specific, personalized recommendations that consider their unique features",
                "Each recommendation should be detailed and tailored to their body type",
                "Include specific clothing items and styles that would work well",
                "Mention colors and patterns that would be flattering",
                "Include advice about silhouettes and proportions"
            ]
        }}

        Important:
        1. Use ONLY the body types listed above
        2. Base your analysis STRICTLY on the provided description
        3. Be specific and personalized in your recommendations
        4. Do not use generic responses
        5. Reference specific details from their description
        6. If the description is unclear, ask for more details
        """
        
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        
        try:
            result = response.text.strip()
            # Clean up the response to ensure it's valid JSON
            result = result.replace("```json", "").replace("```", "").strip()
            parsed_result = json.loads(result)
            
            # Validate the response has the required fields
            if not all(key in parsed_result for key in ["body_type", "detailed_analysis", "style_recommendations"]):
                logger.error(f"Missing required fields in Gemini response: {result}")
                return get_fallback_body_analysis(description)
                
            # Ensure body type is valid
            valid_body_types = [t.lower() for t in BODY_TYPES.keys()]
            if parsed_result["body_type"].lower() not in valid_body_types:
                logger.warning(f"Invalid body type returned by Gemini: {parsed_result['body_type']}")
                logger.warning("Valid types are: " + ", ".join(valid_body_types))
                return get_fallback_body_analysis(description)
                
            return parsed_result
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Gemini response: {str(e)}")
            logger.error(f"Raw response: {result}")
            return get_fallback_body_analysis(description)
            
    except Exception as e:
        logger.error(f"Error in Gemini API call: {str(e)}")
        return get_fallback_body_analysis(description)

def get_fallback_body_analysis(description: str) -> Dict[str, Any]:
    """Provide fallback body type analysis when Gemini API fails"""
    logger.info("Using fallback body analysis with description: " + description)
    description = description.lower()
    
    # Define characteristic keywords for each body type with more specific indicators
    body_type_keywords = {
        "hourglass": [
            "defined waist", "curvy", "hourglass", "balanced", 
            "equal shoulders and hips", "small waist", "curves"
        ],
        "pear": [
            "wider hips", "narrow shoulders", "bottom heavy", "larger bottom",
            "bigger thighs", "smaller top", "heavier bottom"
        ],
        "apple": [
            "fuller middle", "round tummy", "wider waist", "full midsection",
            "carries weight in middle", "broad shoulders", "slim legs"
        ],
        "rectangle": [
            "straight", "athletic", "not curvy", "boyish", "no curves",
            "similar measurements", "undefined waist"
        ],
        "inverted triangle": [
            "broad shoulders", "wide shoulders", "narrow hips", "athletic upper body",
            "v-shaped", "swimmer's build", "bigger top"
        ]
    }
    
    # Count keyword matches for each body type
    body_type_scores = {}
    matched_keywords = {}  # Track which keywords matched for logging
    
    for body_type, keywords in body_type_keywords.items():
        score = 0
        matches = []
        for keyword in keywords:
            if keyword in description:
                score += 1
                matches.append(keyword)
        body_type_scores[body_type] = score
        matched_keywords[body_type] = matches
    
    # Log the matching process
    logger.info("Keyword matching results:")
    for body_type, matches in matched_keywords.items():
        logger.info(f"{body_type}: {len(matches)} matches - {matches}")
    
    # Get the body type with the highest score
    body_type = max(body_type_scores.items(), key=lambda x: x[1])[0]
    
    # If no clear match (score is 0), look for general body characteristics
    if body_type_scores[body_type] == 0:
        logger.warning("No clear body type matches found, analyzing general characteristics")
        if "tall" in description or "long" in description:
            body_type = "rectangle"
        elif "curvy" in description:
            body_type = "hourglass"
        elif "round" in description or "full" in description:
            body_type = "apple"
        else:
            logger.warning("Using rectangle as default body type")
            body_type = "rectangle"
    
    result = BODY_TYPES.get(body_type, BODY_TYPES["rectangle"]).copy()
    result["body_type"] = body_type
    
    # Generate more detailed analysis based on the description
    analysis_parts = []
    
    # Height analysis
    if "tall" in description:
        analysis_parts.append("You have a tall frame")
    elif "short" in description or "petite" in description:
        analysis_parts.append("You have a petite frame")
    elif "average height" in description:
        analysis_parts.append("You have an average height")
    
    # Build analysis
    if "curvy" in description:
        analysis_parts.append("with well-defined curves")
    elif "athletic" in description or "muscular" in description:
        analysis_parts.append("with an athletic build")
    elif "slim" in description or "thin" in description:
        analysis_parts.append("with a slim build")
    
    # Shoulder analysis
    if "shoulders" in description:
        if any(word in description for word in ["broad", "wide", "strong"]):
            analysis_parts.append("and broader shoulders")
        elif "narrow" in description:
            analysis_parts.append("and narrow shoulders")
        else:
            analysis_parts.append("and proportionate shoulders")
    
    # Hip analysis
    if "hips" in description:
        if any(word in description for word in ["wide", "full", "heavy"]):
            analysis_parts.append("with wider hips")
        elif "narrow" in description:
            analysis_parts.append("with narrow hips")
        else:
            analysis_parts.append("with proportionate hips")
    
    # Waist analysis
    if "waist" in description:
        if any(word in description for word in ["defined", "small", "tiny"]):
            analysis_parts.append("and a defined waist")
        elif any(word in description for word in ["thick", "undefined", "straight"]):
            analysis_parts.append("and a less defined waist")
        else:
            analysis_parts.append("and a moderate waist definition")
    
    # Combine analysis parts
    detailed_analysis = " ".join(analysis_parts) if analysis_parts else result["description"]
    result["detailed_analysis"] = f"Based on your description, you appear to have {detailed_analysis}. {result['description']}"
    
    logger.info(f"Fallback analysis complete. Body type: {body_type}")
    logger.info(f"Analysis details: {detailed_analysis}")
    
    return result

def get_gemini_face_analysis(description: str, additional_context: str = None) -> Dict[str, Any]:
    """Get face shape analysis from Gemini AI."""
    if not GOOGLE_API_KEY:
        logger.warning("No API key found, falling back to basic face analysis")
        return get_fallback_face_analysis(description)
    
    try:
        prompt = f"""
        You are a professional facial analysis expert and stylist. Analyze the following face description and provide a detailed, personalized face shape analysis.

        Description: {description}
        {f"Additional Context: {additional_context}" if additional_context else ""}

        Based on the description, determine the most accurate face shape from these options:
        - Oval (balanced proportions, slightly curved jawline)
        - Round (equal width and length, soft angles)
        - Square (strong jawline, equal width and length)
        - Heart (wider forehead, narrower chin)
        - Diamond (narrow forehead and jaw, wider cheekbones)

        Provide a detailed, personalized response in this JSON format:
        {{
            "face_shape": "one of the above types",
            "detailed_analysis": "A personalized analysis that references specific details from their description",
            "style_recommendations": [
                "5 specific, personalized recommendations for hairstyles and accessories",
                "Each recommendation should be detailed and tailored to their face shape",
                "Include specific styles that would work well",
                "Mention face-framing elements that would be flattering",
                "Include advice about proportions and balance"
            ]
        }}

        Important:
        1. Use ONLY the face shapes listed above
        2. Base your analysis STRICTLY on the provided description
        3. Be specific and personalized in your recommendations
        4. Do not use generic responses
        5. Reference specific details from their description
        6. If the description is unclear, ask for more details
        """
        
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        
        try:
            result = response.text.strip()
            # Clean up the response to ensure it's valid JSON
            result = result.replace("```json", "").replace("```", "").strip()
            parsed_result = json.loads(result)
            
            # Validate the response has the required fields
            if not all(key in parsed_result for key in ["face_shape", "detailed_analysis", "style_recommendations"]):
                logger.error(f"Missing required fields in Gemini response: {result}")
                return get_fallback_face_analysis(description)
                
            # Ensure face shape is valid
            valid_face_shapes = [t.lower() for t in FACE_SHAPES.keys()]
            if parsed_result["face_shape"].lower() not in valid_face_shapes:
                logger.warning(f"Invalid face shape returned by Gemini: {parsed_result['face_shape']}")
                logger.warning("Valid shapes are: " + ", ".join(valid_face_shapes))
                return get_fallback_face_analysis(description)
                
            return parsed_result
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Gemini response: {str(e)}")
            logger.error(f"Raw response: {result}")
            return get_fallback_face_analysis(description)
            
    except Exception as e:
        logger.error(f"Error in Gemini API call: {str(e)}")
        return get_fallback_face_analysis(description)

def get_fallback_face_analysis(description: str) -> Dict[str, Any]:
    """Provide fallback face shape analysis when Gemini API fails"""
    logger.info("Using fallback face analysis with description: " + description)
    description = description.lower()
    
    # Define characteristic keywords for each face shape with more specific indicators
    face_shape_keywords = {
        "oval": [
            "balanced", "oval", "egg shaped", "proportional",
            "slightly curved jaw", "medium forehead", "gentle curves"
        ],
        "round": [
            "round", "circular", "soft angles", "full cheeks",
            "equal width length", "curved jaw", "soft features"
        ],
        "square": [
            "square", "angular", "strong jaw", "wide jaw",
            "straight lines", "defined angles", "broad forehead"
        ],
        "heart": [
            "heart shaped", "wide forehead", "narrow chin",
            "pointed chin", "v shaped", "widow's peak"
        ],
        "diamond": [
            "diamond", "angular cheeks", "pointed chin",
            "narrow forehead", "high cheekbones", "narrow jaw"
        ]
    }
    
    # Count keyword matches for each face shape
    face_shape_scores = {}
    matched_keywords = {}  # Track which keywords matched for logging
    
    for shape, keywords in face_shape_keywords.items():
        score = 0
        matches = []
        for keyword in keywords:
            if keyword in description:
                score += 1
                matches.append(keyword)
        face_shape_scores[shape] = score
        matched_keywords[shape] = matches
    
    # Log the matching process
    logger.info("Keyword matching results:")
    for shape, matches in matched_keywords.items():
        logger.info(f"{shape}: {len(matches)} matches - {matches}")
    
    # Get the face shape with the highest score
    face_shape = max(face_shape_scores.items(), key=lambda x: x[1])[0]
    
    # If no clear match (score is 0), analyze general characteristics
    if face_shape_scores[face_shape] == 0:
        logger.warning("No clear face shape matches found, analyzing general characteristics")
        if "long" in description:
            face_shape = "oval"
        elif "round" in description or "full" in description:
            face_shape = "round"
        elif "angular" in description or "strong" in description:
            face_shape = "square"
        else:
            logger.warning("Using oval as default face shape")
            face_shape = "oval"
    
    result = FACE_SHAPES.get(face_shape, FACE_SHAPES["oval"]).copy()
    result["face_shape"] = face_shape
    
    # Generate more detailed analysis based on the description
    analysis_parts = []
    
    # Forehead analysis
    if "forehead" in description:
        if any(word in description for word in ["broad", "wide", "high"]):
            analysis_parts.append("You have a broader forehead")
        elif "narrow" in description:
            analysis_parts.append("You have a narrow forehead")
        else:
            analysis_parts.append("You have a proportionate forehead")
    
    # Cheekbone analysis
    if any(word in description for word in ["cheek", "cheekbone"]):
        if any(word in description for word in ["high", "prominent", "defined"]):
            analysis_parts.append("with high cheekbones")
        elif any(word in description for word in ["full", "round"]):
            analysis_parts.append("with full cheeks")
        else:
            analysis_parts.append("with moderate cheekbone definition")
    
    # Jawline analysis
    if any(word in description for word in ["jaw", "jawline"]):
        if any(word in description for word in ["strong", "angular", "defined"]):
            analysis_parts.append("and a strong jawline")
        elif any(word in description for word in ["soft", "round", "curved"]):
            analysis_parts.append("and a soft jawline")
        else:
            analysis_parts.append("and a moderate jawline")
    
    # Chin analysis
    if "chin" in description:
        if any(word in description for word in ["pointed", "narrow"]):
            analysis_parts.append("with a pointed chin")
        elif any(word in description for word in ["round", "soft"]):
            analysis_parts.append("with a rounded chin")
        elif any(word in description for word in ["square", "strong"]):
            analysis_parts.append("with a square chin")
        else:
            analysis_parts.append("with a balanced chin")
    
    # Overall face length/width analysis
    if any(word in description for word in ["long", "elongated"]):
        analysis_parts.append("Your face is longer than it is wide")
    elif any(word in description for word in ["wide", "broad"]):
        analysis_parts.append("Your face is wider than it is long")
    elif "balanced" in description or "proportional" in description:
        analysis_parts.append("Your face has balanced proportions")
    
    # Combine analysis parts
    detailed_analysis = " ".join(analysis_parts) if analysis_parts else result["description"]
    result["detailed_analysis"] = f"Based on your description, {detailed_analysis}. {result['description']}"
    
    logger.info(f"Fallback analysis complete. Face shape: {face_shape}")
    logger.info(f"Analysis details: {detailed_analysis}")
    
    return result

def get_gemini_color_analysis(description: str, additional_context: str = None) -> Dict[str, Any]:
    """Get color season analysis from Gemini AI."""
    if not GOOGLE_API_KEY:
        logger.warning("No API key found, falling back to basic color analysis")
        return get_fallback_color_analysis(description)
    
    try:
        prompt = f"""
        You are a professional color analyst and personal stylist. Analyze the following description and provide a detailed, personalized color season analysis.

        Description: {description}
        {f"Additional Context: {additional_context}" if additional_context else ""}

        Based on the description, determine the most accurate color season from these options:
        - Spring (warm and bright)
        - Summer (cool and soft)
        - Autumn (warm and muted)
        - Winter (cool and bright)

        Provide a detailed, personalized response in this JSON format:
        {{
            "color_season": "one of the above seasons",
            "detailed_analysis": "A personalized analysis that references specific details from their description",
            "best_colors": [
                "10 specific colors that would be most flattering",
                "Include a mix of neutrals and statement colors",
                "Be specific with color names (e.g., 'deep navy' instead of just 'blue')",
                "Consider both clothing and accessory colors",
                "Include metallic recommendations if relevant"
            ]
        }}

        Important:
        1. Use ONLY the color seasons listed above
        2. Base your analysis STRICTLY on the provided description
        3. Be specific and personalized in your recommendations
        4. Do not use generic responses
        5. Reference specific details from their description
        6. If the description is unclear, ask for more details
        7. Consider skin tone, hair color, and eye color in your analysis
        """
        
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        
        try:
            result = response.text.strip()
            # Clean up the response to ensure it's valid JSON
            result = result.replace("```json", "").replace("```", "").strip()
            parsed_result = json.loads(result)
            
            # Validate the response has the required fields
            if not all(key in parsed_result for key in ["color_season", "detailed_analysis", "best_colors"]):
                logger.error(f"Missing required fields in Gemini response: {result}")
                return get_fallback_color_analysis(description)
                
            # Ensure color season is valid
            valid_seasons = [t.lower() for t in COLOR_SEASONS.keys()]
            if parsed_result["color_season"].lower() not in valid_seasons:
                logger.warning(f"Invalid color season returned by Gemini: {parsed_result['color_season']}")
                logger.warning("Valid seasons are: " + ", ".join(valid_seasons))
                return get_fallback_color_analysis(description)
                
            return parsed_result
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Gemini response: {str(e)}")
            logger.error(f"Raw response: {result}")
            return get_fallback_color_analysis(description)
            
    except Exception as e:
        logger.error(f"Error in Gemini API call: {str(e)}")
        return get_fallback_color_analysis(description)

def get_fallback_color_analysis(description: str) -> Dict[str, Any]:
    """Provide fallback color season analysis when Gemini API fails"""
    logger.info("Using fallback color analysis with description: " + description)
    description = description.lower()
    
    # Define characteristic keywords for each color season with more specific indicators
    color_season_keywords = {
        "spring": [
            "warm undertone", "golden", "peach", "ivory skin",
            "strawberry blonde", "warm blonde", "golden brown eyes",
            "freckles", "peachy", "warm glow"
        ],
        "summer": [
            "cool undertone", "pink", "rosy", "pale skin",
            "ashy blonde", "light brown", "blue eyes",
            "cool blonde", "soft coloring", "muted"
        ],
        "autumn": [
            "warm undertone", "golden brown", "olive", "tan skin",
            "red hair", "auburn", "hazel eyes",
            "copper", "earth tones", "bronze"
        ],
        "winter": [
            "cool undertone", "blue", "pink", "fair skin",
            "dark hair", "black hair", "dark eyes",
            "high contrast", "clear", "bright"
        ]
    }
    
    # Count keyword matches for each color season
    color_season_scores = {}
    matched_keywords = {}  # Track which keywords matched for logging
    
    for season, keywords in color_season_keywords.items():
        score = 0
        matches = []
        for keyword in keywords:
            if keyword in description:
                score += 1
                matches.append(keyword)
        color_season_scores[season] = score
        matched_keywords[season] = matches
    
    # Log the matching process
    logger.info("Keyword matching results:")
    for season, matches in matched_keywords.items():
        logger.info(f"{season}: {len(matches)} matches - {matches}")
    
    # Get the color season with the highest score
    color_season = max(color_season_scores.items(), key=lambda x: x[1])[0]
    
    # If no clear match (score is 0), analyze general characteristics
    if color_season_scores[color_season] == 0:
        logger.warning("No clear color season matches found, analyzing general characteristics")
        
        # Check for warm/cool indicators
        warm_indicators = ["warm", "golden", "yellow", "peach", "orange", "red"]
        cool_indicators = ["cool", "pink", "blue", "purple", "ash"]
        
        warm_score = sum(1 for word in warm_indicators if word in description)
        cool_score = sum(1 for word in cool_indicators if word in description)
        
        # Check for bright/muted indicators
        bright_indicators = ["bright", "clear", "vivid", "intense", "high contrast"]
        muted_indicators = ["muted", "soft", "subtle", "neutral", "low contrast"]
        
        bright_score = sum(1 for word in bright_indicators if word in description)
        muted_score = sum(1 for word in muted_indicators if word in description)
        
        if warm_score > cool_score:
            if bright_score > muted_score:
                color_season = "spring"
            else:
                color_season = "autumn"
        else:
            if bright_score > muted_score:
                color_season = "winter"
            else:
                color_season = "summer"
                
        logger.info(f"Determined color season based on characteristics - Warm: {warm_score}, Cool: {cool_score}, Bright: {bright_score}, Muted: {muted_score}")
    
    result = COLOR_SEASONS.get(color_season, COLOR_SEASONS["spring"]).copy()
    result["color_season"] = color_season
    
    # Generate more detailed analysis based on the description
    analysis_parts = []
    
    # Skin tone analysis
    if "skin" in description:
        if any(word in description for word in ["warm", "golden", "olive", "yellow"]):
            analysis_parts.append("You have warm undertones in your skin")
        elif any(word in description for word in ["cool", "pink", "blue", "red"]):
            analysis_parts.append("You have cool undertones in your skin")
        elif "neutral" in description:
            analysis_parts.append("You have neutral undertones in your skin")
        
        if any(word in description for word in ["fair", "light", "pale"]):
            analysis_parts.append("with a fair complexion")
        elif any(word in description for word in ["medium", "tan"]):
            analysis_parts.append("with a medium complexion")
        elif any(word in description for word in ["dark", "deep"]):
            analysis_parts.append("with a deep complexion")
    
    # Hair color analysis
    if "hair" in description:
        if any(word in description for word in ["blonde", "golden", "strawberry"]):
            analysis_parts.append("blonde hair")
        elif any(word in description for word in ["brown", "brunette"]):
            analysis_parts.append("brown hair")
        elif any(word in description for word in ["black", "dark"]):
            analysis_parts.append("dark hair")
        elif any(word in description for word in ["red", "auburn", "copper"]):
            analysis_parts.append("red hair")
        elif "gray" in description or "silver" in description:
            analysis_parts.append("gray hair")
        
        if "warm" in description:
            analysis_parts.append("with warm tones")
        elif "cool" in description or "ash" in description:
            analysis_parts.append("with cool tones")
    
    # Eye color analysis
    if "eye" in description:
        if "blue" in description:
            analysis_parts.append("and blue eyes")
        elif "green" in description:
            analysis_parts.append("and green eyes")
        elif "brown" in description:
            analysis_parts.append("and brown eyes")
        elif "hazel" in description:
            analysis_parts.append("and hazel eyes")
        
        if "warm" in description:
            analysis_parts.append("with warm undertones")
        elif "cool" in description:
            analysis_parts.append("with cool undertones")
    
    # Combine analysis parts
    detailed_analysis = " ".join(analysis_parts) if analysis_parts else result["description"]
    result["detailed_analysis"] = f"Based on your description, you have {detailed_analysis}. This suggests you are a {color_season} season. {result['description']}"
    
    logger.info(f"Fallback analysis complete. Color season: {color_season}")
    logger.info(f"Analysis details: {detailed_analysis}")
    
    return result

# --- Message Handlers --- 

@body_analysis_protocol.on_message(model=BodyAnalysisRequest, replies={BodyAnalysisResponse, ErrorResponse})
async def handle_body_request(ctx: Context, sender: str, msg: BodyAnalysisRequest):
    """Handle requests for body shape analysis"""
    logger.info(f"Received body analysis request from {sender}")
    try:
        # Use default data if necessary (though the model ensures data exists)
        body_data = msg.data.dict() if msg.data else {
            "weight_distribution": "balanced",
            "shoulder_hip_proportion": "balanced",
            "waist_definition": "slightly_defined",
            "fitting_issue": "too_tight_waist"
        }
        
        # Determine body type
        result = determine_body_type(body_data)
        logger.info(f"Body analysis completed: {result['body_type']}")
        
        # Send the response back
        await ctx.send(
            sender,
            BodyAnalysisResponse(
                success=True,
                body_type=result["body_type"],
                name=result["name"],
                description=result["description"]
            )
        )
    except Exception as e:
        logger.error(f"Error processing body analysis: {e}")
        await ctx.send(sender, ErrorResponse(message=f"Error in body analysis: {e}"))

@body_analysis_protocol.on_message(model=FaceAnalysisRequest, replies={FaceAnalysisResponse, ErrorResponse})
async def handle_face_request(ctx: Context, sender: str, msg: FaceAnalysisRequest):
    """Handle requests for face shape analysis"""
    logger.info(f"Received face analysis request from {sender}")
    try:
        # Use default data if necessary
        face_data = msg.data.dict() if msg.data else {
            "face_length": "medium",
            "jawline": "rounded",
            "forehead_width": "medium",
            "cheekbones": "average"
        }
        
        # Determine face shape
        result = determine_face_shape(face_data)
        logger.info(f"Face analysis completed: {result['face_shape']}")
        
        # Send the response back
        await ctx.send(
            sender,
            FaceAnalysisResponse(
                success=True,
                face_shape=result["face_shape"],
                name=result["name"],
                description=result["description"]
            )
        )
    except Exception as e:
        logger.error(f"Error processing face analysis: {e}")
        await ctx.send(sender, ErrorResponse(message=f"Error in face analysis: {e}"))

@body_analysis_protocol.on_message(model=ColorAnalysisRequest, replies={ColorAnalysisResponse, ErrorResponse})
async def handle_color_request(ctx: Context, sender: str, msg: ColorAnalysisRequest):
    """Handle requests for color season analysis"""
    logger.info(f"Received color analysis request from {sender}")
    try:
        # Use default data if necessary
        color_data = msg.data.dict() if msg.data else {
            "skin_undertone": "neutral",
            "hair_color": "brown",
            "eye_color": "brown",
            "color_preference": "bright"
        }
        
        # Determine color season
        result = determine_color_season(color_data)
        logger.info(f"Color analysis completed: {result['color_season']}")
        
        # Send the response back
        await ctx.send(
            sender,
            ColorAnalysisResponse(
                success=True,
                color_season=result["color_season"],
                name=result["name"],
                description=result["description"]
            )
        )
    except Exception as e:
        logger.error(f"Error processing color analysis: {e}")
        await ctx.send(sender, ErrorResponse(message=f"Error in color analysis: {e}"))

# --- Gemini-Enhanced Message Handlers ---

@body_analysis_protocol.on_message(model=GeminiBodyAnalysisRequest, replies={GeminiBodyAnalysisResponse, ErrorResponse})
async def handle_gemini_body_request(ctx: Context, sender: str, msg: GeminiBodyAnalysisRequest):
    """Handle requests for Gemini-enhanced body shape analysis"""
    logger.info(f"Received Gemini body analysis request from {sender} with description: {msg.description}")
    try:
        # Get analysis from Gemini with the actual user description
        result = get_gemini_body_analysis(msg.description, msg.additional_context)
        logger.info(f"Gemini body analysis completed with result: {result}")
        
        # Ensure we have valid results
        if not result or 'body_type' not in result:
            raise ValueError("Invalid analysis result")
            
        # Send the response back with the actual analysis
        await ctx.send(
            sender,
            GeminiBodyAnalysisResponse(
                success=True,
                body_type=result['body_type'].lower(),
                name=result['body_type'].capitalize(),
                description=result['detailed_analysis'],
                detailed_analysis=result['detailed_analysis'],
                style_recommendations=result['style_recommendations']
            )
        )
    except Exception as e:
        logger.error(f"Error processing Gemini body analysis: {str(e)}")
        await ctx.send(sender, ErrorResponse(message=f"Error in Gemini body analysis: {str(e)}"))

@body_analysis_protocol.on_message(model=GeminiFaceAnalysisRequest, replies={GeminiFaceAnalysisResponse, ErrorResponse})
async def handle_gemini_face_request(ctx: Context, sender: str, msg: GeminiFaceAnalysisRequest):
    """Handle requests for Gemini-enhanced face shape analysis"""
    logger.info(f"Received Gemini face analysis request from {sender} with description: {msg.description}")
    try:
        # Get analysis from Gemini with the actual user description
        result = get_gemini_face_analysis(msg.description, msg.additional_context)
        logger.info(f"Gemini face analysis completed with result: {result}")
        
        # Ensure we have valid results
        if not result or 'face_shape' not in result:
            raise ValueError("Invalid analysis result")
            
        # Send the response back with the actual analysis
        await ctx.send(
            sender,
            GeminiFaceAnalysisResponse(
                success=True,
                face_shape=result['face_shape'].lower(),
                name=result['face_shape'].capitalize(),
                description=result['detailed_analysis'],
                detailed_analysis=result['detailed_analysis'],
                style_recommendations=result['style_recommendations']
            )
        )
    except Exception as e:
        logger.error(f"Error processing Gemini face analysis: {str(e)}")
        await ctx.send(sender, ErrorResponse(message=f"Error in Gemini face analysis: {str(e)}"))

@body_analysis_protocol.on_message(model=GeminiColorAnalysisRequest, replies={GeminiColorAnalysisResponse, ErrorResponse})
async def handle_gemini_color_request(ctx: Context, sender: str, msg: GeminiColorAnalysisRequest):
    """Handle requests for Gemini-enhanced color season analysis"""
    logger.info(f"Received Gemini color analysis request from {sender} with description: {msg.description}")
    try:
        # Get analysis from Gemini with the actual user description
        result = get_gemini_color_analysis(msg.description, msg.additional_context)
        logger.info(f"Gemini color analysis completed with result: {result}")
        
        # Ensure we have valid results
        if not result or 'color_season' not in result:
            raise ValueError("Invalid analysis result")
            
        # Send the response back with the actual analysis
        await ctx.send(
            sender,
            GeminiColorAnalysisResponse(
                success=True,
                color_season=result['color_season'].lower(),
                name=result['color_season'].capitalize(),
                description=result['detailed_analysis'],
                detailed_analysis=result['detailed_analysis'],
                color_palette=result.get('best_colors', [])
            )
        )
    except Exception as e:
        logger.error(f"Error processing Gemini color analysis: {str(e)}")
        await ctx.send(sender, ErrorResponse(message=f"Error in Gemini color analysis: {str(e)}"))

# Include the protocol
body_agent.include(body_analysis_protocol)

# On startup event handler
@body_agent.on_event("startup")
async def startup(ctx: Context):
    """Initialize agent on startup"""
    logger.info(f"Body Analysis Agent started with address: {ctx.address}")

if __name__ == "__main__":
    body_agent.run() 