"""
Main Assistant Agent for AVA Style Assistant
Coordinates communication between different agents and serves as the central hub
"""
from uagents import Agent, Context, Protocol
from uagents.setup import fund_agent_if_low
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import message models
from models.message_models import (
    BodyAnalysisRequest, 
    BodyAnalysisResponse,
    FaceAnalysisRequest,
    FaceAnalysisResponse,
    ColorAnalysisRequest,
    ColorAnalysisResponse,
    StyleRecommendationRequest,
    StyleRecommendationResponse,
    UpcycleTextRequest,
    UpcycleResponse,
    QueryMessage,
    AssistantResponse
)

from utils.helpers import logger

# Agent addresses (to be updated when the agents are started)
BODY_AGENT_ADDRESS = "agent1..."  # Will be updated at runtime
RECOMMENDATION_AGENT_ADDRESS = "agent1..."  # Will be updated at runtime
UPCYCLER_AGENT_ADDRESS = "agent1..."  # Will be updated at runtime

# Define the Assistant Agent
ASSISTANT_AGENT_SEED = "assistant_agent_secret_seed_phrase_must_32_bytes"
assistant_agent = Agent(
    name="ava_assistant",
    seed=ASSISTANT_AGENT_SEED,
    port=8000,
    endpoint=["http://localhost:8000/submit"],
)

# Fund the agent if balance is low
fund_agent_if_low(assistant_agent.wallet.address())

# Create main protocol for the assistant
assistant_protocol = Protocol("AVAStyleAssistant")

# Message handlers for receiving responses from other agents

# Body Analysis Response Handler
@assistant_protocol.on_message(model=BodyAnalysisResponse)
async def handle_body_analysis_response(ctx: Context, sender: str, msg: BodyAnalysisResponse):
    """Handle body analysis responses from the body agent"""
    ctx.logger.info(f"Received body analysis response from {sender}: {msg.body_type}")
    
    # Store the result
    ctx.storage.set("last_body_analysis", {
        "body_type": msg.body_type,
        "name": msg.name,
        "description": msg.description
    })
    
    # Check if we should automatically proceed to face analysis
    auto_proceed = ctx.storage.get("auto_proceed_analysis", False)
    if auto_proceed:
        ctx.logger.info("Auto-proceeding to face analysis")
        await request_face_analysis(ctx)

# Face Analysis Response Handler
@assistant_protocol.on_message(model=FaceAnalysisResponse)
async def handle_face_analysis_response(ctx: Context, sender: str, msg: FaceAnalysisResponse):
    """Handle face analysis responses from the body agent"""
    ctx.logger.info(f"Received face analysis response from {sender}: {msg.face_shape}")
    
    # Store the result
    ctx.storage.set("last_face_analysis", {
        "face_shape": msg.face_shape,
        "name": msg.name,
        "description": msg.description
    })
    
    # Check if we should automatically proceed to color analysis
    auto_proceed = ctx.storage.get("auto_proceed_analysis", False)
    if auto_proceed:
        ctx.logger.info("Auto-proceeding to color analysis")
        await request_color_analysis(ctx)

# Color Analysis Response Handler
@assistant_protocol.on_message(model=ColorAnalysisResponse)
async def handle_color_analysis_response(ctx: Context, sender: str, msg: ColorAnalysisResponse):
    """Handle color analysis responses from the body agent"""
    ctx.logger.info(f"Received color analysis response from {sender}: {msg.color_season}")
    
    # Store the result
    ctx.storage.set("last_color_analysis", {
        "color_season": msg.color_season,
        "name": msg.name,
        "description": msg.description
    })
    
    # Check if we should automatically proceed to style recommendations
    auto_proceed = ctx.storage.get("auto_proceed_analysis", False)
    if auto_proceed:
        ctx.logger.info("Auto-proceeding to style recommendations")
        await request_style_recommendations(ctx)

# Style Recommendation Response Handler
@assistant_protocol.on_message(model=StyleRecommendationResponse)
async def handle_style_recommendation_response(ctx: Context, sender: str, msg: StyleRecommendationResponse):
    """Handle style recommendation responses from the recommendation agent"""
    ctx.logger.info(f"Received style recommendations from {sender}")
    
    # Store the result
    ctx.storage.set("last_style_recommendations", msg.recommendations)
    
    # Save request complete status
    ctx.storage.set("style_request_complete", True)

# Upcycler Response Handler
@assistant_protocol.on_message(model=UpcycleResponse)
async def handle_upcycle_response(ctx: Context, sender: str, msg: UpcycleResponse):
    """Handle upcycling responses from the upcycler agent"""
    ctx.logger.info(f"Received upcycling ideas from {sender}")
    
    # Store the result
    ctx.storage.set("last_upcycle_ideas", msg.ideas)
    
    # Save request complete status
    ctx.storage.set("upcycle_request_complete", True)

# User query handler
@assistant_protocol.on_message(model=QueryMessage, replies={AssistantResponse})
async def handle_user_query(ctx: Context, sender: str, msg: QueryMessage):
    """Handle query messages from users"""
    ctx.logger.info(f"Received query from {sender}: {msg.query}")
    
    query = msg.query.lower().strip()
    
    # Determine what type of query this is
    if any(word in query for word in ["body", "shape", "figure", "silhouette"]):
        # Body analysis request
        ctx.logger.info("Interpreting as body analysis request")
        ctx.storage.set("auto_proceed_analysis", False)  # Don't auto-proceed
        await request_body_analysis(ctx)
        response = AssistantResponse(
            response="I've started a body shape analysis for you. I'll let you know when the results are ready."
        )
        
    elif any(word in query for word in ["face", "features", "jaw", "forehead"]):
        # Face analysis request
        ctx.logger.info("Interpreting as face analysis request")
        ctx.storage.set("auto_proceed_analysis", False)  # Don't auto-proceed
        await request_face_analysis(ctx)
        response = AssistantResponse(
            response="I've started a face shape analysis for you. I'll let you know when the results are ready."
        )
        
    elif any(word in query for word in ["color", "season", "palette", "tone"]):
        # Color analysis request
        ctx.logger.info("Interpreting as color analysis request")
        ctx.storage.set("auto_proceed_analysis", False)  # Don't auto-proceed
        await request_color_analysis(ctx)
        response = AssistantResponse(
            response="I've started a color season analysis for you. I'll let you know when the results are ready."
        )
        
    elif any(word in query for word in ["style", "fashion", "outfit", "recommendation", "trend"]):
        # Style recommendation request
        ctx.logger.info("Interpreting as style recommendation request")
        ctx.storage.set("auto_proceed_analysis", False)  # Don't auto-proceed
        await request_style_recommendations(ctx)
        response = AssistantResponse(
            response="I'm getting some style recommendations for you based on your profile. I'll let you know when they're ready."
        )
        
    elif any(word in query for word in ["upcycle", "recycle", "reuse", "repurpose"]):
        # Upcycling request
        ctx.logger.info("Interpreting as upcycling request")
        await request_upcycling_ideas(ctx, query)
        response = AssistantResponse(
            response="I'm looking for creative ways to upcycle your clothing item. I'll share ideas shortly."
        )
        
    elif any(word in query for word in ["complete", "full", "all"]):
        # Complete analysis request (body, face, color, then style)
        ctx.logger.info("Interpreting as complete analysis request")
        ctx.storage.set("auto_proceed_analysis", True)  # Auto-proceed through all steps
        await request_body_analysis(ctx)
        response = AssistantResponse(
            response="I'm starting a complete style analysis for you. This will include body shape, face shape, color season, and personalized style recommendations."
        )
    
    else:
        # General query - provide help
        response = AssistantResponse(
            response="I can help you with body shape analysis, face shape analysis, color season analysis, style recommendations, or upcycling ideas. What would you like to know about?"
        )
    
    await ctx.send(sender, response)

# Functions to request analyses from other agents
async def request_body_analysis(ctx: Context):
    """Request body shape analysis from the body agent"""
    # In a real implementation, this would use actual user data
    # For this example, we'll use some default values
    request = BodyAnalysisRequest(
        weight_distribution="even",
        shoulder_hip_proportion="balanced",
        waist_definition="defined",
        fitting_issue="none"
    )
    
    ctx.logger.info(f"Requesting body analysis from {BODY_AGENT_ADDRESS}")
    await ctx.send(BODY_AGENT_ADDRESS, request)

async def request_face_analysis(ctx: Context):
    """Request face shape analysis from the body agent"""
    # In a real implementation, this would use actual user data
    request = FaceAnalysisRequest(
        face_length="long",
        jawline="rounded",
        forehead_width="medium",
        cheekbones="balanced"
    )
    
    ctx.logger.info(f"Requesting face analysis from {BODY_AGENT_ADDRESS}")
    await ctx.send(BODY_AGENT_ADDRESS, request)

async def request_color_analysis(ctx: Context):
    """Request color season analysis from the body agent"""
    # In a real implementation, this would use actual user data
    request = ColorAnalysisRequest(
        skin_undertone="cool",
        hair_color="dark_brown",
        eye_color="brown",
        color_preference="bright"
    )
    
    ctx.logger.info(f"Requesting color analysis from {BODY_AGENT_ADDRESS}")
    await ctx.send(BODY_AGENT_ADDRESS, request)

async def request_style_recommendations(ctx: Context):
    """Request style recommendations from the recommendation agent"""
    # Get the analysis results from storage, or use defaults
    body_analysis = ctx.storage.get("last_body_analysis", {})
    face_analysis = ctx.storage.get("last_face_analysis", {})
    color_analysis = ctx.storage.get("last_color_analysis", {})
    
    body_type = body_analysis.get("body_type", "hourglass")
    face_shape = face_analysis.get("face_shape", "oval")
    color_season = color_analysis.get("color_season", "winter")
    
    request = StyleRecommendationRequest(
        body_type=body_type,
        face_shape=face_shape,
        color_season=color_season
    )
    
    ctx.logger.info(f"Requesting style recommendations from {RECOMMENDATION_AGENT_ADDRESS}")
    await ctx.send(RECOMMENDATION_AGENT_ADDRESS, request)

async def request_upcycling_ideas(ctx: Context, query):
    """Request upcycling ideas from the upcycler agent"""
    request = UpcycleTextRequest(
        text=query
    )
    
    ctx.logger.info(f"Requesting upcycling ideas from {UPCYCLER_AGENT_ADDRESS}")
    await ctx.send(UPCYCLER_AGENT_ADDRESS, request)

# Register the protocol with the agent
assistant_agent.include(assistant_protocol)

# Startup event handler
@assistant_agent.on_event("startup")
async def on_startup(ctx: Context):
    """Handle agent startup - initialize storage and log status"""
    logger.info(f"AVA Assistant Agent started with address: {assistant_agent.address}")
    
    # Initialize storage
    ctx.storage.set("auto_proceed_analysis", False)
    ctx.storage.set("style_request_complete", False)
    ctx.storage.set("upcycle_request_complete", False)

# Function to update agent addresses
def update_agent_addresses(body_address, recommendation_address, upcycler_address):
    """Update the addresses of the other agents"""
    global BODY_AGENT_ADDRESS, RECOMMENDATION_AGENT_ADDRESS, UPCYCLER_AGENT_ADDRESS
    
    BODY_AGENT_ADDRESS = body_address
    RECOMMENDATION_AGENT_ADDRESS = recommendation_address
    UPCYCLER_AGENT_ADDRESS = upcycler_address
    
    logger.info(f"Updated agent addresses: Body={body_address}, Recommendation={recommendation_address}, Upcycler={upcycler_address}")

if __name__ == "__main__":
    logger.info(f"Starting assistant agent with address: {assistant_agent.address}")
    assistant_agent.run() 