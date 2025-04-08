"""
Face Shape Analysis Agent for AVA Style Assistant
This redirects to the body_agent.py since we're combining body, face, and color analysis
"""
from uagents import Agent, Context, Protocol
from utils.helpers import logger

# This is just a placeholder since the functionality is in body_agent.py
# The body_agent handles all three types of analysis: body, face, and color
face_agent = Agent(
    name="face_analyzer",
    seed="face_analyzer_agent_seed_phrase_must_be_32_bytes"
)

if __name__ == "__main__":
    logger.info("Face analysis is handled by body_agent.py")
    logger.info("Please run body_agent.py instead.") 