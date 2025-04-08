from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import logging
import google.generativeai as genai
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("stylist_server")

# Configure Gemini API with your API key
GOOGLE_API_KEY = "AIzaSyAeLz-VMv8FCXuPHdip1YZZUEmdMcIOCaA"  # Replace with your actual API key
genai.configure(api_key=GOOGLE_API_KEY)

# Use Gemini model
MODEL_NAME = "models/gemini-1.5-flash"

def load_product_database():
    """Load the product database from a JSON file"""
    try:
        with open('data/products.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Product database not found. Creating an empty database.")
        
        # Create the data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Create a basic empty database structure
        default_db = {
            "dresses": [],
            "tops": [],
            "bottoms": [],
            "outerwear": [],
            "shoes": [],
            "accessories": []
        }
        
        # Create a sample product
        sample_product = {
            "id": "sample001",
            "name": "Sample Dress",
            "description": "This is a sample product",
            "imageUrl": "https://m.media-amazon.com/images/I/71KMBidjcDL._AC_UL1500_.jpg",
            "price": "₹999",
            "retailer": "Sample Store",
            "link": "https://www.amazon.com",
            "bodyTypes": ["hourglass", "pear", "triangle", "apple"],
            "colorSeasons": ["autumn", "winter"],
            "occasions": ["casual", "office"]
        }
        
        # Add the sample product to the database
        default_db["dresses"].append(sample_product)
        
        # Save the default database
        with open('data/products.json', 'w') as f:
            json.dump(default_db, f, indent=2)
            
        return default_db
    except Exception as e:
        logger.error(f"Error loading product database: {e}")
        return {
            "dresses": [],
            "tops": [],
            "bottoms": [],
            "outerwear": [],
            "shoes": [],
            "accessories": []
        }

def get_style_recommendations(profile, clothing_type=None, occasion=None):
    """
    Get style recommendations for the user based on their profile.
    Uses both Gemini for general advice and a product database for specific items.
    """
    # Format the user profile for Gemini
    body_type = profile.get("bodyType", "unknown")
    face_shape = profile.get("faceShape", "unknown")
    color_season = profile.get("colorSeason", "unknown")
    
    # Create a prompt for Gemini to generate style advice
    prompt = f"""
    As a professional fashion stylist, provide personalized style recommendations for someone with the following characteristics:
    
    Body Type: {body_type}
    Face Shape: {face_shape}
    Color Season: {color_season}
    
    Please provide:
    1. An overall style direction that would flatter this body type
    2. Specific clothing recommendations (cuts, styles, fits)
    3. Colors that would look great based on their color season
    4. What to avoid for this body type
    
    {f"Focus specifically on {clothing_type}." if clothing_type else ""}
    {f"These recommendations should be suitable for {occasion} occasions." if occasion else ""}
    
    Format your advice to be concise, specific, and directly applicable.
    """
    
    try:
        # Call Gemini for style advice
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        style_advice = response.text
        
        # Load product database
        products_db = load_product_database()
        
        # Filter and select relevant products
        selected_products = []
        
        # If clothing type is specified, only look at those products
        if clothing_type and clothing_type in products_db:
            categories = [clothing_type]
        else:
            categories = list(products_db.keys())
        
        # Select products from each relevant category
        for category in categories:
            if category in products_db:
                # Filter by body type
                matching_products = [p for p in products_db[category] 
                                    if p.get("bodyTypes") and body_type.lower() in [t.lower() for t in p.get("bodyTypes")]]
                
                # Then filter by color season if available
                if color_season != "unknown":
                    color_matching = [p for p in matching_products 
                                     if p.get("colorSeasons") and color_season.lower() in [c.lower() for c in p.get("colorSeasons")]]
                    if color_matching:  # Only use color-filtered results if there are any
                        matching_products = color_matching
                
                # Filter by occasion if specified
                if occasion:
                    occasion_matching = [p for p in matching_products 
                                        if p.get("occasions") and occasion.lower() in [o.lower() for o in p.get("occasions")]]
                    if occasion_matching:  # Only use occasion-filtered results if there are any
                        matching_products = occasion_matching
                
                # Add a random selection of up to 3 products from each category
                import random
                if matching_products:
                    selected = random.sample(matching_products, min(3, len(matching_products)))
                    selected_products.extend(selected)
        
        # If no products match the criteria, add some default products
        if not selected_products and products_db:
            for category in categories:
                if category in products_db and products_db[category]:
                    # Add one random product from each category
                    import random
                    if products_db[category]:
                        selected_products.append(random.choice(products_db[category]))
        
        # Return results
        return {
            "recommendations": selected_products,
            "styleAdvice": style_advice,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating style recommendations: {e}")
        # Return fallback recommendations
        return {
            "recommendations": [],
            "styleAdvice": get_fallback_style_advice(body_type, color_season),
            "timestamp": datetime.now().isoformat()
        }

def get_fallback_style_advice(body_type, color_season):
    """Provide fallback style advice when Gemini API fails"""
    advice = "Here are some general style recommendations:\n\n"
    
    # Body type advice
    if body_type == "hourglass":
        advice += "For your hourglass shape, look for clothes that emphasize your waist. Wrap dresses, belted jackets, and fitted tops are great choices.\n\n"
    elif body_type == "rectangle":
        advice += "For your rectangle shape, create the illusion of curves with peplum tops, full skirts, and layers to add dimension.\n\n"
    elif body_type == "triangle" or body_type == "pear":
        advice += "For your triangle/pear shape, balance your proportions with statement tops, wider necklines, and A-line skirts.\n\n"
    elif body_type == "invertedTriangle" or body_type == "inverted-triangle":
        advice += "For your inverted triangle shape, balance your proportions with fuller bottoms, A-line skirts, and details at the hip.\n\n"
    elif body_type == "apple":
        advice += "For your apple shape, create definition with empire waists, V-necks, and structured pieces that create a vertical line.\n\n"
    else:
        advice += "Focus on pieces that make you feel comfortable and confident. A-line silhouettes and vertical details are universally flattering.\n\n"
    
    # Color season advice
    if color_season == "winter":
        advice += "As a Winter, you look best in clear, bright colors with blue undertones. Try jewel tones like emerald, sapphire, and ruby."
    elif color_season == "summer":
        advice += "As a Summer, you look best in soft, muted colors with blue undertones. Try lavender, powder blue, and soft rose."
    elif color_season == "autumn":
        advice += "As an Autumn, you look best in warm, muted earth tones. Try olive green, terracotta, and golden yellow."
    elif color_season == "spring":
        advice += "As a Spring, you look best in warm, clear colors. Try coral, peach, and bright golden yellow."
    else:
        advice += "Choose colors that make you feel confident. Neutrals like navy, black, and white work for everyone."
    
    return advice

class StylistRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the stylist agent"""
    
    def _send_response(self, status_code, data):
        """Send a JSON response with CORS headers"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        # Ensure data is properly serialized to JSON
        if isinstance(data, str):
            self.wfile.write(data.encode('utf-8'))
        else:
            self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override log_message to use our logger"""
        logger.info("%s - - [%s] %s" % (self.client_address[0], self.log_date_time_string(), format % args))
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health':
            self._send_response(200, {"status": "ok", "agent": "stylist_agent", "version": "1.0.0"})
            logger.info("Health check request received and responded")
        elif self.path == '/debug':
            # Return detailed debug information
            debug_info = {
                "status": "running",
                "agent": "stylist_agent",
                "version": "1.0.0",
                "google_api_key_configured": bool(GOOGLE_API_KEY),
                "product_database_loaded": bool(load_product_database()),
                "timestamp": str(datetime.now()),
                "environment": {
                    "python_version": sys.version,
                    "platform": sys.platform
                }
            }
            self._send_response(200, debug_info)
            logger.info("Debug info request received and responded")
        elif self.path == '/test':
            # Return a test response with sample products
            test_data = {
                "recommendations": [
                    {
                        "id": "test001",
                        "name": "Test Product",
                        "description": "This is a test product to verify the API works",
                        "imageUrl": "https://m.media-amazon.com/images/I/71KMBidjcDL._AC_UL1500_.jpg",
                        "price": "₹999",
                        "retailer": "Test Store",
                        "link": "https://www.amazon.com"
                    }
                ],
                "styleAdvice": "This is a test style advice to verify the API works without using Gemini.",
                "timestamp": datetime.now().isoformat()
            }
            self._send_response(200, test_data)
            logger.info("Test request received and responded")
        else:
            self._send_response(404, {"error": "Not found"})
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            # Read request data
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            request_json = json.loads(post_data)
            
            logger.info(f"Received POST request to {self.path}")
            logger.info(f"Request data: {post_data}")
            
            if self.path == '/recommend':
                # Extract profile information
                profile = request_json.get('profile', {})
                clothing_type = request_json.get('clothingType')
                occasion = request_json.get('occasion')
                
                # Log request details
                logger.info(f"Processing recommendations for profile: {profile}")
                logger.info(f"Clothing type: {clothing_type}, Occasion: {occasion}")
                
                # Get style recommendations
                recommendations = get_style_recommendations(profile, clothing_type, occasion)
                logger.info(f"Generated {len(recommendations.get('recommendations', []))} recommendations")
                
                # Send response
                self._send_response(200, recommendations)
            else:
                logger.warning(f"Unknown endpoint requested: {self.path}")
                self._send_response(404, {"error": "Endpoint not found"})
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
            self._send_response(400, {"error": "Invalid JSON"})
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            self._send_response(500, {"error": str(e)})

# --- Main ---

if __name__ == "__main__":
    # Start HTTP server
    port = 6000
    try:
        server = HTTPServer(('', port), StylistRequestHandler)
        logger.info(f"Starting HTTP server on port {port}")
        
        # Print startup message
        print("\n=== Stylist & Trend Analyst Server Starting ===")
        print(f"\nUsing Gemini model: {MODEL_NAME}")
        print(f"\nAPI Key configured: {bool(GOOGLE_API_KEY)}")
        print("\nTo get style recommendations, send a POST request to http://localhost:6000/recommend")
        print("Example request:")
        print('{"profile": {"bodyType": "hourglass", "faceShape": "oval", "colorSeason": "winter"}}')
        print("\nTest endpoint available at http://localhost:6000/test")
        print("\nServer is running on http://localhost:6000")
        
        # Start the server
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.server_close()
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        print(f"Error starting server: {e}")
        sys.exit(1) 