from uagents import Bureau
import os
import sys
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("bureau")

# Import agent creation functions from agent modules
sys.path.append('agents')
try:
    from agents.stylist_agent import create_agent as create_stylist_agent
    from agents.upcycler_agent import create_agent as create_upcycler_agent
    from agents.recommendation_agent import recommendation_agent
    from agents.stylist_agent import StylistRequestHandler
    from agents.upcycler_agent import UpcyclerRequestHandler
    from agents.recommendation_handler import RecommendationRequestHandler
except ImportError as e:
    logger.error(f"Error importing agent modules: {e}")
    logger.error("Make sure the agents directory contains all required agent files")
    sys.exit(1)

# Create a Bureau to manage our agents
bureau = Bureau(endpoint="http://127.0.0.1:8000", port=8000)

def start_web_server():
    """Start a simple HTTP server for the web frontend"""
    logger.info("Starting web server on port 8080")
    
    # Custom handler to set correct content types
    class AVAWebHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory='.', **kwargs)
            
        def log_message(self, format, *args):
            # Redirect logs to our logger
            logger.info("%s - - [%s] %s" % (self.client_address[0], 
                                        self.log_date_time_string(), 
                                        format % args))
            
        def end_headers(self):
            # Add CORS headers to allow frontend to call our APIs
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            super().end_headers()
    
    web_server = HTTPServer(('', 8080), AVAWebHandler)
    try:
        web_server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Web server stopped")
        web_server.server_close()

def start_stylist_server():
    """Start the stylist agent HTTP server"""
    try:
        stylist_agent = create_stylist_agent()
        bureau.add(stylist_agent)
        
        # Create and start the HTTP server for the stylist agent
        server = HTTPServer(('', 6000), StylistRequestHandler)
        logger.info("Starting Stylist Agent HTTP server on port 6000")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Error starting stylist agent: {e}")

def start_upcycler_server():
    """Start the upcycler agent HTTP server"""
    try:
        upcycler_agent = create_upcycler_agent()
        bureau.add(upcycler_agent)
        
        # Create and start the HTTP server for the upcycler agent
        server = HTTPServer(('', 5000), UpcyclerRequestHandler)
        logger.info("Starting Upcycler Agent HTTP server on port 5000")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Error starting upcycler agent: {e}")

def start_recommendation_server():
    """Start the recommendation agent HTTP server"""
    try:
        bureau.add(recommendation_agent)
        
        # Create and start the HTTP server for the recommendation agent
        server = HTTPServer(('', 8002), RecommendationRequestHandler)
        logger.info("Starting Recommendation Agent HTTP server on port 8002")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Error starting recommendation agent: {e}")

if __name__ == "__main__":
    try:
        # Print startup banner
        print("\n===================================")
        print("   AVA Style Assistant Bureau")
        print("===================================\n")
        
        # Check if API keys are configured
        if not os.environ.get("GOOGLE_API_KEY"):
            logger.warning("GOOGLE_API_KEY environment variable not set. Some AI features may not work.")
            logger.warning("To use AI features, create a .env file with your Google API key.")
        
        # Start each component in a separate thread
        web_thread = threading.Thread(target=start_web_server, daemon=True)
        web_thread.start()
        logger.info("Web server thread started")
        
        stylist_thread = threading.Thread(target=start_stylist_server, daemon=True)
        stylist_thread.start()
        logger.info("Stylist agent thread started")
        
        upcycler_thread = threading.Thread(target=start_upcycler_server, daemon=True)
        upcycler_thread.start()
        logger.info("Upcycler agent thread started")
        
        recommendation_thread = threading.Thread(target=start_recommendation_server, daemon=True)
        recommendation_thread.start()
        logger.info("Recommendation agent thread started")
        
        # Print helpful information
        print("\nAVA Style Assistant is now running:")
        print("- Web Frontend: http://localhost:8080")
        print("- Stylist Agent API: http://localhost:6000")
        print("- Upcycler Agent API: http://localhost:5000")
        print("- Recommendation Agent API: http://localhost:8002")
        print("\nPress Ctrl+C to quit\n")
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down AVA Style Assistant")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1) 