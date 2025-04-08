import os
import sys
import logging
import socket
import threading
import time
import asyncio
from http.server import HTTPServer
from agents.simplified_agent import SimpleRequestHandler, create_agent
from agents.upcycler_agent import UpcyclerRequestHandler, create_agent as create_upcycler_agent
from agents.stylist_agent import StylistRequestHandler, create_agent as create_stylist_agent
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("run")

def is_port_in_use(port):
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_available_port(start_port, max_attempts=20):
    """Find an available port starting from start_port"""
    port = start_port
    for _ in range(max_attempts):
        if not is_port_in_use(port):
            return port
        port += 1
    raise RuntimeError(f"Could not find an available port after {max_attempts} attempts starting from {start_port}")

def start_web_server(port, handler_class):
    """Start a web server with the specified handler class"""
    try:
        server = HTTPServer(('', port), handler_class)
        logger.info(f'Starting server on http://localhost:{port}')
        logger.info(f'Health check endpoint: http://localhost:{port}/health')
        server.serve_forever()
    except OSError as e:
        if e.errno == 98 or e.errno == 10048:  # Address already in use (Linux/Windows)
            logger.error(f"Port {port} is already in use. Please close the application using this port or choose a different port.")
            sys.exit(1)
        else:
            logger.error(f"Error starting web server: {e}")
            raise

def start_body_scanner_agent():
    """Start the body scanner agent and its HTTP server"""
    try:
        # Create the agent
        agent = create_agent()
        logger.info(f"Body Scanner Agent created with address: {agent.address}")
        
        # Find an available port
        port = int(os.environ.get('BODY_SCANNER_PORT', 8002))
        if is_port_in_use(port):
            port = find_available_port(port)
            logger.info(f"Using port {port} for Body Scanner Agent server")
            
        # Start the web server in a separate thread
        server_thread = threading.Thread(
            target=start_web_server,
            args=(port, SimpleRequestHandler),
            daemon=True
        )
        server_thread.start()
        
    except Exception as e:
        logger.error(f"Error in Body Scanner Agent: {e}", exc_info=True)

def start_upcycler_agent():
    """Start the upcycler agent and its HTTP server"""
    try:
        # Create the agent
        agent = create_upcycler_agent()
        logger.info(f"Upcycler Agent created with address: {agent.address}")
        
        # Find an available port
        port = int(os.environ.get('UPCYCLER_PORT', 5000))
        if is_port_in_use(port):
            port = find_available_port(port)
            logger.info(f"Using port {port} for Upcycler Agent server")
            
        # Start the web server in a separate thread
        server_thread = threading.Thread(
            target=start_web_server,
            args=(port, UpcyclerRequestHandler),
            daemon=True
        )
        server_thread.start()
        
    except Exception as e:
        logger.error(f"Error in Upcycler Agent: {e}", exc_info=True)

def start_stylist_agent():
    """Start the stylist agent and its HTTP server"""
    try:
        # Create the agent
        agent = create_stylist_agent()
        logger.info(f"Stylist Agent created with address: {agent.address}")
        
        # Find an available port
        port = int(os.environ.get('STYLIST_PORT', 6000))
        if is_port_in_use(port):
            port = find_available_port(port)
            logger.info(f"Using port {port} for Stylist Agent server")
        
        # Start the web server directly in this thread - non-blocking approach
        from http.server import HTTPServer
        from agents.stylist_agent import StylistRequestHandler
        
        server = HTTPServer(('', port), StylistRequestHandler)
        logger.info(f"Starting server on http://localhost:{port}")
        logger.info(f"Health check endpoint: http://localhost:{port}/health")
        
        # Run the server in a separate thread
        import threading
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
    except Exception as e:
        logger.error(f"Error in Stylist Agent: {e}", exc_info=True)

if __name__ == '__main__':
    logger.info("Starting AVA Style Assistant agents with fetch.ai...")
    logger.info("Press Ctrl+C to stop all services")

    try:
        # Start all agents in separate threads
        body_scanner_thread = threading.Thread(
            target=start_body_scanner_agent,
            daemon=True
        )
        body_scanner_thread.start()
        
        upcycler_thread = threading.Thread(
            target=start_upcycler_agent,
            daemon=True
        )
        upcycler_thread.start()
        
        stylist_thread = threading.Thread(
            target=start_stylist_agent,
            daemon=True
        )
        stylist_thread.start()
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down all services...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1) 