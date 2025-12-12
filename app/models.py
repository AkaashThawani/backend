from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, JSON, DateTime, Text, create_engine
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from datetime import datetime

Base = declarative_base()

# Master Tables for reusable data
class MasterKeyword(Base):
    __tablename__ = "master_keywords"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MasterSubreddit(Base):
    __tablename__ = "master_subreddits"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)  # e.g. "r/startups"
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MasterPersona(Base):
    __tablename__ = "master_personas"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    backstory = Column(Text)
    tone_style = Column(String, default="Professional")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    goal = Column(String, nullable=True) # e.g. "Brand Awareness"
    company_name = Column(String)
    company_info = Column(JSON) # { website, description, usps }
    status = Column(String, default="DRAFT") # DRAFT, ACTIVE, COMPLETED, PAUSED
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    personas = relationship("Persona", back_populates="campaign")
    targeting = relationship("TargetingConfig", back_populates="campaign", uselist=False)
    schedule_settings = relationship("ScheduleSettings", back_populates="campaign", uselist=False)
    posts = relationship("Post", back_populates="campaign")

class Persona(Base):
    __tablename__ = "personas"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    username = Column(String)
    backstory = Column(String)
    tone_style = Column(String)
    is_active = Column(Boolean, default=True)
    
    campaign = relationship("Campaign", back_populates="personas")

class TargetingConfig(Base):
    __tablename__ = "targeting"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    subreddits = Column(JSON) # LIst of strings
    keywords = Column(JSON) # List of strings
    ai_custom_prompts = Column(String, nullable=True)
    
    campaign = relationship("Campaign", back_populates="targeting")

class ScheduleSettings(Base):
    __tablename__ = "schedule_settings"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    posts_per_week = Column(Integer)
    max_posts_per_week = Column(Integer, default=5)  # NEW
    max_comments_per_post = Column(Integer, default=3)  # NEW
    company_mention_rate = Column(Integer, default=30)  # NEW: 0-100%
    mention_in_posts = Column(Boolean, default=False)  # NEW
    mention_in_comments = Column(Boolean, default=True)  # NEW
    timezone = Column(String, default="UTC")
    active_days = Column(JSON) # [1, 2, 3...]

    campaign = relationship("Campaign", back_populates="schedule_settings")

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    subreddit = Column(String)
    title = Column(String)
    body = Column(String)
    author_username = Column(String) # Denormalized for display ease, or link to persona? let's keep string for flexibility
    scheduled_time = Column(DateTime)
    status = Column(String) # PLANNED, POSTED
    keyword_ids = Column(JSON) # List of IDs
    
    campaign = relationship("Campaign", back_populates="posts")
    comments = relationship("Comment", back_populates="post")

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"))
    parent_comment_id = Column(Integer, nullable=True) # If null, it's a top level comment on the post
    author_username = Column(String)
    content = Column(String)
    scheduled_time = Column(DateTime)
    posted_at = Column(DateTime, nullable=True)
    status = Column(String, default="SCHEDULED")

    post = relationship("Post", back_populates="comments")

# Advanced Features Tables
class SubredditCategory(Base):
    __tablename__ = "subreddit_categories"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)  # "presentation_tools"
    display_name = Column(String)  # "Presentation Tools"
    description = Column(String, nullable=True)
    subreddits = Column(JSON)  # ["r/PowerPoint", "r/GoogleSlides"]

class KeywordTheme(Base):
    __tablename__ = "keyword_themes"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)  # "problem_solving"
    display_name = Column(String)  # "Problem Solving"
    description = Column(String, nullable=True)
    keywords = Column(JSON)  # ["K1", "K5", "K11"]

class PersonaCategoryPreference(Base):
    __tablename__ = "persona_category_preferences"

    id = Column(Integer, primary_key=True)
    persona_id = Column(Integer, ForeignKey("personas.id"))
    category_name = Column(String)

    persona = relationship("Persona")

class CampaignAdvancedSettings(Base):
    __tablename__ = "campaign_advanced_settings"

    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), unique=True)
    max_posts_per_subreddit_week = Column(Integer, default=2)
    min_hours_between_posts = Column(Integer, default=24)
    min_uniqueness_score = Column(Integer, default=70)
    min_relevance_score = Column(Integer, default=80)
    require_manual_approval = Column(String, default="never")
    avoid_similar_titles = Column(Boolean, default=True)
    rotate_personas_evenly = Column(Boolean, default=True)
    balance_keyword_themes = Column(Boolean, default=True)

    campaign = relationship("Campaign")

class ContentReviewItem(Base):
    __tablename__ = "content_review_items"

    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    content_type = Column(String)  # "post" or "comment"
    content_id = Column(Integer)
    status = Column(String, default="pending")
    uniqueness_score = Column(Integer, nullable=True)
    relevance_score = Column(Integer, nullable=True)
    authenticity_score = Column(Integer, nullable=True)
    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    campaign = relationship("Campaign")

# Database Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./reddit_mastermind.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
