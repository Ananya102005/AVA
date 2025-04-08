from uagents import Model
from typing import Dict, List, Optional, Any

# --- General Models ---
class ErrorResponse(Model):
    success: bool = False
    message: str

# --- Body Agent Models ---

# Request Data Structures
class BodyAnalysisData(Model):
    weight_distribution: str
    shoulder_hip_proportion: str
    waist_definition: str
    fitting_issue: str

class FaceAnalysisData(Model):
    face_length: str
    jawline: str
    forehead_width: str
    cheekbones: str

class ColorAnalysisData(Model):
    skin_undertone: str
    hair_color: str
    eye_color: str
    color_preference: str

# New Gemini-enhanced request models
class GeminiBodyAnalysisRequest(Model):
    type: str = "gemini_body_analysis_request"
    description: str
    additional_context: Optional[str] = None

class GeminiFaceAnalysisRequest(Model):
    type: str = "gemini_face_analysis_request"
    description: str
    additional_context: Optional[str] = None

class GeminiColorAnalysisRequest(Model):
    type: str = "gemini_color_analysis_request"
    description: str
    additional_context: Optional[str] = None

# Request Models (Wrapping the data and adding a type)
class BodyAnalysisRequest(Model):
    type: str = "body_analysis_request" # To help the handler differentiate
    data: BodyAnalysisData

class FaceAnalysisRequest(Model):
    type: str = "face_analysis_request"
    data: FaceAnalysisData

class ColorAnalysisRequest(Model):
    type: str = "color_analysis_request"
    data: ColorAnalysisData
    
# Combined Request Model (Alternative if using one handler)
# class AnalysisRequest(Model):
#     type: str # 'body_analysis_request', 'face_analysis_request', 'color_analysis_request'
#     data: Dict[str, Any] 

# Response Models
class BodyAnalysisResponse(Model):
    type: str = "body_analysis_response"
    success: bool
    body_type: str
    name: str
    description: str

class FaceAnalysisResponse(Model):
    type: str = "face_analysis_response"
    success: bool
    face_shape: str
    name: str
    description: str

class ColorAnalysisResponse(Model):
    type: str = "color_analysis_response"
    success: bool
    color_season: str
    name: str
    description: str

# New Gemini-enhanced response models
class GeminiBodyAnalysisResponse(Model):
    type: str = "gemini_body_analysis_response"
    success: bool
    body_type: str
    name: str
    description: str
    detailed_analysis: str
    style_recommendations: List[str]

class GeminiFaceAnalysisResponse(Model):
    type: str = "gemini_face_analysis_response"
    success: bool
    face_shape: str
    name: str
    description: str
    detailed_analysis: str
    style_recommendations: List[str]

class GeminiColorAnalysisResponse(Model):
    type: str = "gemini_color_analysis_response"
    success: bool
    color_season: str
    name: str
    description: str
    detailed_analysis: str
    color_palette: List[str]

# --- Recommendation Agent Models ---
class StyleRecommendationRequest(Model):
    """Request model for style recommendations"""
    body_type: str
    face_shape: str
    color_season: str

class StyleRecommendationResponse(Model):
    """Response model for style recommendations"""
    # Structure based on how it's used in recommendation_agent.py
    recommendations: Dict[str, List[Any]] # Includes 'products' list and advice categories
    success: bool = True
    error: Optional[str] = None

# --- Upcycler Agent Models ---
class UpcycleRequest(Model):
    type: str = "upcycle_request"
    item: str
    max_ideas: int = 3

class UpcycleResponse(Model):
    type: str = "upcycle_response"
    success: bool
    ideas: List[str]
    message: Optional[str] = None

# --- Assistant Agent Models --- 
class UserQuery(Model):
    type: str = "user_query"
    query: str

class AssistantResponse(Model):
    type: str = "response"
    message: str

class UserProfileRequest(Model):
    """Request to create or update a user profile"""
    user_id: str
    body_analysis: Optional[Dict[str, Any]] = None
    face_analysis: Optional[Dict[str, Any]] = None
    color_analysis: Optional[Dict[str, Any]] = None

class UserProfileResponse(Model):
    """Response with user profile information"""
    user_id: str
    profile_complete: bool
    body_analysis: Optional[Dict[str, Any]] = None
    face_analysis: Optional[Dict[str, Any]] = None
    color_analysis: Optional[Dict[str, Any]] = None
    success: bool = True
    error: Optional[str] = None 