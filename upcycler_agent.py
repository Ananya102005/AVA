"""
Upcycler Agent for AVA Style Assistant
Handles generating upcycling ideas for clothing items using Gemini AI
"""
from uagents import Agent, Context, Protocol
from uagents.setup import fund_agent_if_low
import os
import sys
from datetime import datetime
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import message models
from models.message_models import (
    UpcycleTextRequest,
    UpcycleResponse
)

from utils.helpers import logger, extract_clothing_item

# Load environment variables
load_dotenv()

# Configure Gemini API
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    logger.info("Gemini API configured successfully for upcycler agent")
else:
    logger.warning("GOOGLE_API_KEY not set. Using fallback upcycling ideas.")

# Use Gemini model
MODEL_NAME = "models/gemini-1.5-flash"

# Define upcycler agent with secure seed
UPCYCLER_AGENT_SEED = "upcycler_agent_secret_seed_phrase_must_32_bytes_"
agent = Agent(
    name="upcycler",
    seed=UPCYCLER_AGENT_SEED,
    port=8003,
    endpoint=["http://localhost:8003/submit"],
)

# Fund the agent if balance is low
fund_agent_if_low(agent.wallet.address())

# Create protocol for upcycling ideas
upcycler_protocol = Protocol("UpcyclerIdeas")

# Helper functions
def get_gemini_upcycling_ideas(item_text):
    """Get creative upcycling ideas from Gemini AI."""
    if not GOOGLE_API_KEY:
        return get_fallback_ideas(item_text)
    
    try:
        prompt = f"""
        Generate 5 creative and practical upcycling ideas for an old {item_text}. 
        For each idea:
        1. Provide a clear title
        2. Give a brief description
        3. List required materials
        4. Outline the key steps
        
        Format each idea to be clear and separate from others.
        """
        
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        return [response.text]
    
    except Exception as e:
        logger.error(f"Error in Gemini API call: {str(e)}")
        return get_fallback_ideas(item_text)

def get_fallback_ideas(item_text):
    """Provide fallback upcycling ideas when Gemini API fails"""
    
    # Dictionary of common clothing items and ideas
    fallback_ideas = {
        "jeans": [
            "1. Denim Tote Bag\n   - Cut the legs off old jeans and sew the bottom to create a stylish tote bag.\n   - Materials: Old jeans, scissors, sewing machine, thread, decorative buttons (optional)\n   - Steps: Cut off legs, sew bottom closed, add handles from remaining fabric, decorate as desired.",
            
            "2. Jean Patch Quilt\n   - Cut squares from multiple pairs of jeans to create a durable quilt.\n   - Materials: Multiple old jeans, scissors, sewing machine, quilt batting, backing fabric\n   - Steps: Cut uniform squares, arrange in pattern, sew together, add batting and backing, quilt as desired.",
            
            "3. Denim Plant Pot Covers\n   - Use jean legs as decorative covers for plain plant pots.\n   - Materials: Jean legs, scissors, glue or needle and thread\n   - Steps: Cut jean legs to desired length, hem or fold one end, slip over pots, secure with decorative belt or ribbon."
        ],
        
        "shirt": [
            "1. No-Sew T-shirt Tote Bag\n   - Transform an old t-shirt into a functional bag without sewing.\n   - Materials: Old t-shirt, scissors\n   - Steps: Cut off sleeves, cut wider neck opening, cut fringe at bottom, tie fringe to close bottom.",
            
            "2. T-shirt Yarn for Knitting/Crochet\n   - Create yarn from old shirts for various craft projects.\n   - Materials: Old t-shirts, sharp scissors\n   - Steps: Cut shirts in continuous spiral strips, stretch strips to create yarn, use for knitting or crochet projects.",
            
            "3. Pillow Cover\n   - Convert a meaningful t-shirt into a decorative pillow.\n   - Materials: T-shirt with design, scissors, sewing machine, pillow form, thread\n   - Steps: Cut shirt to size, sew with design centered, leave opening for pillow form, insert form, sew closed."
        ],
        
        "sweater": [
            "1. Cozy Winter Mittens\n   - Create warm mittens from old sweaters.\n   - Materials: Wool sweater (preferably felted), scissors, needle and thread, mitten pattern\n   - Steps: Felt sweater if not already felted, cut mitten shapes, sew together, add decorative stitching if desired.",
            
            "2. Sweater Pet Bed\n   - Make a comfortable pet bed from an old sweater.\n   - Materials: Large sweater, scissors, needle and thread, pillow stuffing or old pillows\n   - Steps: Sew sleeve openings closed, sew neck partially closed, stuff with filling, sew remaining openings.",
            
            "3. Sweater Slippers\n   - Convert a cozy sweater into warm house slippers.\n   - Materials: Wool sweater, scissors, needle and thread, fabric for soles\n   - Steps: Cut foot shapes, sew together with decorative stitching, add non-slip fabric to soles."
        ],
        
        "dress": [
            "1. Child's Dress or Skirt\n   - Resize an adult dress for a child.\n   - Materials: Adult dress, scissors, sewing machine, elastic for waistband\n   - Steps: Cut to child's size, hem appropriately, add elastic waistband if needed, reuse original details like buttons.",
            
            "2. Decorative Pillow Covers\n   - Use dress fabric to create unique pillow covers.\n   - Materials: Dress with interesting fabric, scissors, sewing machine, pillow forms\n   - Steps: Cut fabric to size plus seam allowance, sew sides, add zipper or envelope closure, insert pillow form.",
            
            "3. Fabric Jewelry\n   - Create fabric jewelry from dress details.\n   - Materials: Dress with beading/sequins/interesting fabric, scissors, jewelry findings, glue\n   - Steps: Cut decorative elements, attach to jewelry findings, add clasps or hooks as needed."
        ]
    }
    
    # Default fallback for unknown items
    default_ideas = [
        "1. Fabric Flowers\n   - Create decorative flowers from any clothing.\n   - Materials: Old clothing, scissors, needle and thread, buttons for centers\n   - Steps: Cut fabric into circles of various sizes, layer, stitch center to create flower shape, add button center.",
        
        "2. Wall Art Hanging\n   - Frame interesting fabric or clothing parts.\n   - Materials: Clothing with patterns/textures, embroidery hoop or frame, scissors\n   - Steps: Cut fabric to size, stretch in embroidery hoop or frame, display individually or in groupings.",
        
        "3. Fabric Rag Rug\n   - Create a textured rug from clothing scraps.\n   - Materials: Various old clothing, scissors, rug canvas or mesh\n   - Steps: Cut fabric into strips, tie or weave through rug canvas in patterns, trim edges for neat finish."
    ]
    
    # Return ideas for the specific item if available, or default ideas
    return fallback_ideas.get(item_text.lower(), default_ideas)

# Upcycler request handler
@upcycler_protocol.on_message(model=UpcycleTextRequest, replies={UpcycleResponse})
async def handle_upcycle_request(ctx: Context, sender: str, msg: UpcycleTextRequest):
    """Handle upcycling idea requests"""
    ctx.logger.info(f"Received upcycling request from {sender}")
    
    try:
        # Extract the clothing item from the text
        item = extract_clothing_item(msg.text)
        ctx.logger.info(f"Processing upcycling ideas for: {item}")
        
        # Get ideas from Gemini or fallback
        if GOOGLE_API_KEY:
            ideas = get_gemini_upcycling_ideas(item)
        else:
            ideas = get_fallback_ideas(item)
        
        # Create response with ideas
        response = UpcycleResponse(
            ideas=ideas,
            success=True
        )
        
        ctx.logger.info(f"Upcycling ideas generated for: {item}")
        await ctx.send(sender, response)
        
    except Exception as e:
        ctx.logger.error(f"Error processing upcycling request: {str(e)}")
        error_response = UpcycleResponse(
            ideas=[f"Error generating upcycling ideas: {str(e)}"],
            success=False,
            error=f"Upcycling idea generation failed: {str(e)}"
        )
        await ctx.send(sender, error_response)

# Register protocol with the agent
agent.include(upcycler_protocol)

if __name__ == "__main__":
    logger.info(f"Starting upcycler agent with address: {agent.address}")
    agent.run() 