from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class PersonaCreate(BaseModel):
    username: str  # Changed from 'name' to match frontend
    backstory: str
    tone_style: Optional[str] = "Professional"

class KeywordItem(BaseModel):
    id: str
    keyword: str

class CampaignCreate(BaseModel):
    # Step 1: Company
    company_name: str
    company_site: str
    company_description: str

    # Step 2: Campaign details
    campaign_name: str

    # Step 3: Personas
    personas: List[PersonaCreate]

    # Step 4: Strategy
    subreddits: List[str]  # Changed from comma-separated string to array
    keywords: List[KeywordItem]  # Changed from comma-separated string to array of objects
    max_posts_per_week: int = 5  # CHANGED from posts_per_week
    max_comments_per_post: int = 3  # NEW
    company_mention_rate: int = 30  # NEW: 0-100%
    mention_in_posts: bool = False  # NEW
    mention_in_comments: bool = True  # NEW
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    # Advanced features (optional)
    subreddit_categories: Optional[Dict[str, List[str]]] = None
    keyword_themes: Optional[Dict[str, List[str]]] = None
    persona_category_preferences: Optional[Dict[str, List[str]]] = None
    advanced_settings: Optional[Dict[str, Any]] = None

class CampaignResponse(BaseModel):
    id: int
    name: str
    status: str
    class Config:
        orm_mode = True
