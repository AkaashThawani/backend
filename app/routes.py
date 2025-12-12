from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime
from app.models import (
    SessionLocal, init_db, Campaign, Persona, TargetingConfig, ScheduleSettings,
    Post, Comment, MasterKeyword, MasterSubreddit, MasterPersona,
    SubredditCategory, KeywordTheme, PersonaCategoryPreference,
    CampaignAdvancedSettings, ContentReviewItem
)

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize DB on import (simple for this MVP)
init_db()

@router.get("/campaigns")
def list_campaigns(db: Session = Depends(get_db)):
    campaigns = db.query(Campaign).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "status": c.status,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "company_name": c.company_name
        }
        for c in campaigns
    ]

from app.schemas import CampaignCreate, CampaignResponse

@router.post("/campaigns", response_model=CampaignResponse)
def create_campaign(data: CampaignCreate, db: Session = Depends(get_db)):
    # 1. Create Campaign
    from datetime import datetime
    
    start_dt = datetime.fromisoformat(data.start_date) if data.start_date else None
    end_dt = datetime.fromisoformat(data.end_date) if data.end_date else None

    new_campaign = Campaign(
        name=data.campaign_name,
        company_name=data.company_name,
        company_info={
            "website": data.company_site,
            "description": data.company_description
        },
        status="ACTIVE",
        start_date=start_dt,
        end_date=end_dt
    )
    db.add(new_campaign)
    db.commit()
    db.refresh(new_campaign)

    # 2. Add Personas
    for p in data.personas:
        new_persona = Persona(
            campaign_id=new_campaign.id,
            username=p.username,  # Changed from p.name to p.username
            backstory=p.backstory,
            tone_style=p.tone_style or "Professional"
        )
        db.add(new_persona)
    
    # 3. Add Targeting
    subreddits_list = data.subreddits  # Already a list
    keywords_list = [k.keyword for k in data.keywords]  # Extract keyword strings from KeywordItem objects
    
    new_targeting = TargetingConfig(
        campaign_id=new_campaign.id,
        subreddits=subreddits_list,
        keywords=keywords_list
    )
    db.add(new_targeting)

    # 4. Add Schedule
    new_schedule = ScheduleSettings(
        campaign_id=new_campaign.id,
        posts_per_week=data.max_posts_per_week,  # Keep for compatibility
        max_posts_per_week=data.max_posts_per_week,
        max_comments_per_post=data.max_comments_per_post,
        company_mention_rate=data.company_mention_rate,
        mention_in_posts=data.mention_in_posts,
        mention_in_comments=data.mention_in_comments,
        active_days=[0,1,2,3,4] # Mon-Fri default
    )
    db.add(new_schedule)

    db.commit()
    return new_campaign

@router.get("/campaigns/{campaign_id}")
def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """Get complete campaign details with posts and comments"""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Load all related data
    personas = db.query(Persona).filter(Persona.campaign_id == campaign_id).all()
    targeting = db.query(TargetingConfig).filter(TargetingConfig.campaign_id == campaign_id).first()
    schedule = db.query(ScheduleSettings).filter(ScheduleSettings.campaign_id == campaign_id).first()
    posts = db.query(Post).filter(Post.campaign_id == campaign_id).all()
    
    # Build posts with their comments
    posts_with_comments = []
    for post in posts:
        comments = db.query(Comment).filter(Comment.post_id == post.id).all()
        posts_with_comments.append({
            "id": post.id,
            "subreddit": post.subreddit,
            "title": post.title,
            "body": post.body,
            "author_username": post.author_username,
            "scheduled_time": post.scheduled_time.isoformat() if post.scheduled_time else None,
            "status": post.status,
            "keyword_ids": post.keyword_ids or [],  # ✅ ADD THIS: Return keyword_ids from database
            "comments": [
                {
                    "id": c.id,
                    "content": c.content,
                    "author_username": c.author_username,
                    "scheduled_time": c.scheduled_time.isoformat() if c.scheduled_time else None,
                    "parent_comment_id": c.parent_comment_id
                }
                for c in comments
            ]
        })
    
    return {
        "id": campaign.id,
        "name": campaign.name,
        "company_name": campaign.company_name,
        "company_info": campaign.company_info,
        "status": campaign.status,
        "start_date": campaign.start_date.isoformat() if campaign.start_date else None,
        "end_date": campaign.end_date.isoformat() if campaign.end_date else None,
        "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
        "personas": [
            {
                "id": p.id,
                "username": p.username,
                "backstory": p.backstory,
                "tone_style": p.tone_style
            }
            for p in personas
        ],
        "targeting": {
            "subreddits": targeting.subreddits if targeting else [],
            "keywords": targeting.keywords if targeting else []
        } if targeting else None,
        "schedule": {
            "posts_per_week": schedule.posts_per_week if schedule else 0,
            "max_posts_per_week": schedule.max_posts_per_week if schedule else 5,
            "max_comments_per_post": schedule.max_comments_per_post if schedule else 3,
            "active_days": schedule.active_days if schedule else []
        } if schedule else None,
        "posts": posts_with_comments
    }

@router.get("/campaigns/{campaign_id}/posts")
def get_campaign_posts(campaign_id: int, db: Session = Depends(get_db)):
    posts = db.query(Post).filter(Post.campaign_id == campaign_id).all()
    return [
        {
            "id": p.id,
            "subreddit": p.subreddit,
            "title": p.title,
            "body": p.body,
            "author_username": p.author_username,
            "scheduled_time": p.scheduled_time.isoformat() if p.scheduled_time else None,
            "status": p.status
        }
        for p in posts
    ]

@router.get("/health")
def health_check():
    """Simple health check endpoint for deployment monitoring"""
    return {
        "status": "healthy",
        "service": "ogtool-algo-backend",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
    # Real metrics from database
    total_personas = db.query(Persona).count()
    total_posts = db.query(Post).count()
    total_comments = db.query(Comment).count()
    total_campaigns = db.query(Campaign).count()
    active_campaigns = db.query(Campaign).filter(Campaign.status == "ACTIVE").count()
    
    return {
        "total_personas": total_personas,
        "total_posts": total_posts,
        "total_comments": total_comments,
        "total_campaigns": total_campaigns,
        "active_campaigns": active_campaigns,
        "system_health": "Operational"
    }

from app.algorithm import ContentCalendarGenerator, Persona as AlgoPersona

@router.post("/campaigns/{campaign_id}/generate")
def generate_schedule(campaign_id: int, db: Session = Depends(get_db)):
    """
    Generate a content calendar for the specified campaign.
    Uses the algorithm to create posts and comments.
    """
    print(f"\n{'='*60}")
    print(f"📥 RECEIVED GENERATE REQUEST FOR CAMPAIGN {campaign_id}")
    print(f"{'='*60}\n")
    
    # 1. Load campaign data
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    print(f"✓ Campaign found: {campaign.name}")
    
    # 2. Load related data
    personas_db = db.query(Persona).filter(Persona.campaign_id == campaign_id).all()
    targeting = db.query(TargetingConfig).filter(TargetingConfig.campaign_id == campaign_id).first()
    schedule = db.query(ScheduleSettings).filter(ScheduleSettings.campaign_id == campaign_id).first()
    
    print(f"✓ Loaded {len(personas_db)} personas")
    print(f"✓ Targeting config: {targeting is not None}")
    print(f"✓ Schedule config: {schedule is not None}")
    
    if not personas_db or len(personas_db) < 2:
        print("❌ ERROR: Need at least 2 personas")
        raise HTTPException(status_code=400, detail="Need at least 2 personas")
    
    if not targeting or not targeting.subreddits:
        print("❌ ERROR: No subreddits configured")
        raise HTTPException(status_code=400, detail="No subreddits configured")
    
    # 3. Convert to algorithm format
    algo_personas = [
        AlgoPersona(
            username=p.username,
            backstory=p.backstory or "",
            tone_style=p.tone_style or "Professional"
        )
        for p in personas_db
    ]
    
    company_info = {
        "name": campaign.company_name,
        "description": campaign.company_info.get("description", "") if campaign.company_info else "",
        "website": campaign.company_info.get("website", "") if campaign.company_info else ""
    }
    
    # Build keywords from targeting (or use defaults)
    keywords = [{"id": f"K{i+1}", "keyword": kw} for i, kw in enumerate(targeting.keywords or ["AI tool", "automation"])]
    
    # Determine which week to generate for
    existing_posts = db.query(Post).filter(Post.campaign_id == campaign_id).all()
    
    if existing_posts:
        # Find the latest scheduled time from ALL posts and comments
        from datetime import timedelta
        
        latest_times = [p.scheduled_time for p in existing_posts if p.scheduled_time]
        
        # Also get all comments for these posts
        for post in existing_posts:
            comments = db.query(Comment).filter(Comment.post_id == post.id).all()
            latest_times.extend([c.scheduled_time for c in comments if c.scheduled_time])
        
        if latest_times:
            latest_date = max(latest_times)
            # Next week starts 1 day after the latest scheduled item
            next_week_start = latest_date + timedelta(days=1)
            
            print(f"✓ Latest scheduled item: {latest_date}")
            print(f"✓ Generating for week starting: {next_week_start}")
        else:
            # Fallback if no times found
            from datetime import datetime
            next_week_start = campaign.start_date.replace(hour=9, minute=0, second=0, microsecond=0) if campaign.start_date else datetime.now()
            print(f"✓ No existing times, using: {next_week_start}")
    else:
        # First generation - use campaign start date
        if campaign.start_date:
            next_week_start = campaign.start_date.replace(hour=9, minute=0, second=0, microsecond=0)
            print(f"✓ First generation - using campaign start date: {next_week_start}")
        else:
            # Fallback to next Monday
            from datetime import datetime, timedelta
            today = datetime.now()
            days_ahead = (7 - today.weekday()) % 7 or 7
            next_week_start = today + timedelta(days=days_ahead)
            next_week_start = next_week_start.replace(hour=9, minute=0, second=0, microsecond=0)
            print(f"✓ No start date - using next Monday: {next_week_start}")
    
    # 4. Run the algorithm with deduplication
    generator = ContentCalendarGenerator(
        company_info=company_info,
        personas=algo_personas,
        subreddits=targeting.subreddits,
        keywords=keywords,
        max_posts_per_week=schedule.max_posts_per_week if schedule else 5,
        max_comments_per_post=schedule.max_comments_per_post if schedule else 3,
        company_mention_rate=schedule.company_mention_rate if schedule else 30,
        posts_per_week=schedule.posts_per_week if schedule else 3,  # Keep for compatibility
        week_start=next_week_start,
        existing_posts=existing_posts  # Pass existing posts for deduplication
    )
    
    calendar = generator.generate()
    
    # 5. Save posts to database
    post_id_map = {}  # Map P1, P2 -> actual DB IDs
    print(f"\n💾 Saving {len(calendar.posts)} posts to database...")
    
    for post in calendar.posts:
        db_post = Post(
            campaign_id=campaign_id,
            subreddit=post.subreddit,
            title=post.title,
            body=post.body,
            author_username=post.author_username,
            scheduled_time=post.scheduled_time,
            status="SCHEDULED",
            keyword_ids=post.keyword_ids
        )
        db.add(db_post)
        db.flush()  # Get the ID
        post_id_map[post.post_id] = db_post.id
        print(f"  ✓ Saved post {post.post_id} → DB ID {db_post.id}")
    
    db.commit()  # Commit posts first
    print(f"✅ All {len(calendar.posts)} posts committed to database\n")
    
    # 6. Save comments to database with validation
    comment_id_map = {}
    failed_comments = []
    
    print(f"💾 Saving {len(calendar.comments)} comments to database...")
    
    for comment in calendar.comments:
        # Validate post_id exists
        db_post_id = post_id_map.get(comment.post_id)
        if db_post_id is None:
            failed_comments.append({
                "comment_id": comment.comment_id,
                "post_id": comment.post_id,
                "reason": "post_id not found in map"
            })
            print(f"  ❌ FAILED: Comment {comment.comment_id} - post {comment.post_id} not found!")
            continue
        
        # Resolve parent comment ID
        parent_db_id = None
        if comment.parent_comment_id:
            parent_db_id = comment_id_map.get(comment.parent_comment_id)
            if parent_db_id is None:
                print(f"  ⚠️ WARNING: Parent comment {comment.parent_comment_id} not found for {comment.comment_id}")
        
        try:
            db_comment = Comment(
                post_id=db_post_id,
                parent_comment_id=parent_db_id,
                content=comment.content,
                author_username=comment.author_username,
                scheduled_time=comment.scheduled_time
            )
            db.add(db_comment)
            db.flush()
            comment_id_map[comment.comment_id] = db_comment.id
            print(f"  ✓ Saved comment {comment.comment_id} → DB ID {db_comment.id}")
        except Exception as e:
            failed_comments.append({
                "comment_id": comment.comment_id,
                "post_id": comment.post_id,
                "error": str(e)
            })
            print(f"  ❌ ERROR saving comment {comment.comment_id}: {e}")
    
    db.commit()
    print(f"✅ Saved {len(comment_id_map)}/{len(calendar.comments)} comments to database")
    
    if failed_comments:
        print(f"\n⚠️ WARNING: {len(failed_comments)} comments failed to save:")
        for failed in failed_comments:
            print(f"  - {failed}")
    
    return {
        "status": "success",
        "posts_created": len(calendar.posts),
        "comments_created": len(calendar.comments),
        "week_start": calendar.week_start.isoformat(),
        "week_end": calendar.week_end.isoformat()
    }


# ============================================
# MASTER DATA ENDPOINTS
# ============================================

# Keywords CRUD
@router.get("/master/keywords")
def list_keywords(db: Session = Depends(get_db)):
    return db.query(MasterKeyword).filter(MasterKeyword.is_active == True).all()

@router.post("/master/keywords")
def create_keyword(keyword: str, description: str = None, db: Session = Depends(get_db)):
    # Check if already exists
    existing = db.query(MasterKeyword).filter(MasterKeyword.keyword == keyword).first()
    if existing:
        raise HTTPException(status_code=400, detail="Keyword already exists")
    
    new_keyword = MasterKeyword(keyword=keyword, description=description)
    db.add(new_keyword)
    db.commit()
    db.refresh(new_keyword)
    return new_keyword

@router.put("/master/keywords/{keyword_id}")
def update_keyword(keyword_id: int, keyword: str = None, description: str = None, is_active: bool = None, db: Session = Depends(get_db)):
    db_keyword = db.query(MasterKeyword).filter(MasterKeyword.id == keyword_id).first()
    if not db_keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    
    if keyword is not None:
        db_keyword.keyword = keyword
    if description is not None:
        db_keyword.description = description
    if is_active is not None:
        db_keyword.is_active = is_active
    
    db_keyword.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_keyword)
    return db_keyword

@router.delete("/master/keywords/{keyword_id}")
def delete_keyword(keyword_id: int, db: Session = Depends(get_db)):
    db_keyword = db.query(MasterKeyword).filter(MasterKeyword.id == keyword_id).first()
    if not db_keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    
    db.delete(db_keyword)
    db.commit()
    return {"status": "deleted"}


# Subreddits CRUD
@router.get("/master/subreddits")
def list_subreddits(db: Session = Depends(get_db)):
    return db.query(MasterSubreddit).filter(MasterSubreddit.is_active == True).all()

@router.post("/master/subreddits")
def create_subreddit(name: str, description: str = None, db: Session = Depends(get_db)):
    # Check if already exists
    existing = db.query(MasterSubreddit).filter(MasterSubreddit.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Subreddit already exists")
    
    new_subreddit = MasterSubreddit(name=name, description=description)
    db.add(new_subreddit)
    db.commit()
    db.refresh(new_subreddit)
    return new_subreddit

@router.put("/master/subreddits/{subreddit_id}")
def update_subreddit(subreddit_id: int, name: str = None, description: str = None, is_active: bool = None, db: Session = Depends(get_db)):
    db_subreddit = db.query(MasterSubreddit).filter(MasterSubreddit.id == subreddit_id).first()
    if not db_subreddit:
        raise HTTPException(status_code=404, detail="Subreddit not found")
    
    if name is not None:
        db_subreddit.name = name
    if description is not None:
        db_subreddit.description = description
    if is_active is not None:
        db_subreddit.is_active = is_active
    
    db_subreddit.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_subreddit)
    return db_subreddit

@router.delete("/master/subreddits/{subreddit_id}")
def delete_subreddit(subreddit_id: int, db: Session = Depends(get_db)):
    db_subreddit = db.query(MasterSubreddit).filter(MasterSubreddit.id == subreddit_id).first()
    if not db_subreddit:
        raise HTTPException(status_code=404, detail="Subreddit not found")
    
    db.delete(db_subreddit)
    db.commit()
    return {"status": "deleted"}


# Personas CRUD
@router.get("/master/personas")
def list_master_personas(db: Session = Depends(get_db)):
    return db.query(MasterPersona).filter(MasterPersona.is_active == True).all()

@router.post("/master/personas")
def create_master_persona(username: str, backstory: str, tone_style: str = "Professional", db: Session = Depends(get_db)):
    # Check if already exists
    existing = db.query(MasterPersona).filter(MasterPersona.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Persona already exists")
    
    new_persona = MasterPersona(username=username, backstory=backstory, tone_style=tone_style)
    db.add(new_persona)
    db.commit()
    db.refresh(new_persona)
    return new_persona

@router.put("/master/personas/{persona_id}")
def update_master_persona(persona_id: int, username: str = None, backstory: str = None, tone_style: str = None, is_active: bool = None, db: Session = Depends(get_db)):
    db_persona = db.query(MasterPersona).filter(MasterPersona.id == persona_id).first()
    if not db_persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    if username is not None:
        db_persona.username = username
    if backstory is not None:
        db_persona.backstory = backstory
    if tone_style is not None:
        db_persona.tone_style = tone_style
    if is_active is not None:
        db_persona.is_active = is_active
    
    db_persona.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_persona)
    return db_persona

@router.delete("/master/personas/{persona_id}")
def delete_master_persona(persona_id: int, db: Session = Depends(get_db)):
    db_persona = db.query(MasterPersona).filter(MasterPersona.id == persona_id).first()
    if not db_persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    db.delete(db_persona)
    db.commit()
    return {"status": "deleted"}

# ============================================
# ADVANCED FEATURES ENDPOINTS
# ============================================

# Subreddit Categories
@router.get("/master/subreddit-categories")
def list_subreddit_categories(db: Session = Depends(get_db)):
    # Return predefined categories (could be made dynamic later)
    return [
        {
            "name": "presentation_tools",
            "display_name": "Presentation Tools",
            "description": "Subreddits focused on presentation software and tools",
            "subreddits": ["r/PowerPoint", "r/GoogleSlides", "r/Canva", "r/presentations"]
        },
        {
            "name": "ai_tools",
            "display_name": "AI Tools",
            "description": "Subreddits focused on AI-powered tools and automation",
            "subreddits": ["r/ChatGPT", "r/ClaudeAI", "r/ChatGPTPro", "r/artificial"]
        },
        {
            "name": "business_general",
            "display_name": "Business General",
            "description": "General business and entrepreneurship subreddits",
            "subreddits": ["r/entrepreneur", "r/startups", "r/smallbusiness", "r/business"]
        },
        {
            "name": "consulting_professional",
            "display_name": "Consulting & Professional",
            "description": "Professional consulting and productivity subreddits",
            "subreddits": ["r/consulting", "r/marketing", "r/productivity"]
        },
        {
            "name": "education_academic",
            "display_name": "Education & Academic",
            "description": "Education and academic presentation subreddits",
            "subreddits": ["r/AskAcademia", "r/teachers", "r/education"]
        },
        {
            "name": "design_creative",
            "display_name": "Design & Creative",
            "description": "Design and creative tool subreddits",
            "subreddits": ["r/design", "r/contentcreation"]
        }
    ]

# Keyword Themes
@router.get("/master/keyword-themes")
def list_keyword_themes(db: Session = Depends(get_db)):
    # Return predefined themes (could be made dynamic later)
    return [
        {
            "name": "problem_solving",
            "display_name": "Problem Solving",
            "description": "Keywords related to solving presentation challenges",
            "keywords": ["best ai presentation maker", "how to make slides faster", "design help for slides", "need help with pitch deck"]
        },
        {
            "name": "comparisons",
            "display_name": "Comparisons",
            "description": "Keywords comparing different tools and platforms",
            "keywords": ["Claude vs Slideforge", "Canva alternative", "PowerPoint alternative", "Google Slides alternative"]
        },
        {
            "name": "specific_use_cases",
            "display_name": "Specific Use Cases",
            "description": "Keywords for specific presentation needs",
            "keywords": ["pitch deck generator", "automate my presentations", "tools for consultants", "tools for startups"]
        },
        {
            "name": "advanced_features",
            "display_name": "Advanced Features",
            "description": "Keywords about advanced presentation features",
            "keywords": ["ai slide deck tool", "slide automation", "best ai design tool", "best storytelling tool"]
        }
    ]

# Content Review Queue
@router.get("/campaigns/{campaign_id}/review-queue")
def get_review_queue(campaign_id: int, db: Session = Depends(get_db)):
    """Get pending content review items for a campaign"""
    items = db.query(ContentReviewItem).filter(
        ContentReviewItem.campaign_id == campaign_id,
        ContentReviewItem.status == "pending"
    ).all()

    result = []
    for item in items:
        # Get the actual content (post or comment)
        if item.content_type == "post":
            content = db.query(Post).filter(Post.id == item.content_id).first()
            if content:
                result.append({
                    "id": item.id,
                    "type": "post",
                    "content": {
                        "title": content.title,
                        "body": content.body,
                        "subreddit": content.subreddit
                    },
                    "quality_scores": {
                        "uniqueness": item.uniqueness_score,
                        "relevance": item.relevance_score,
                        "authenticity": item.authenticity_score
                    }
                })
        elif item.content_type == "comment":
            content = db.query(Comment).filter(Comment.id == item.content_id).first()
            if content:
                result.append({
                    "id": item.id,
                    "type": "comment",
                    "content": {
                        "text": content.content,
                        "post_id": content.post_id
                    },
                    "quality_scores": {
                        "uniqueness": item.uniqueness_score,
                        "relevance": item.relevance_score,
                        "authenticity": item.authenticity_score
                    }
                })

    return result

@router.post("/campaigns/{campaign_id}/review/{item_id}")
def review_content_item(
    campaign_id: int,
    item_id: int,
    action: str,  # "approve", "reject", "regenerate"
    notes: str = None,
    db: Session = Depends(get_db)
):
    """Review a content item (approve, reject, or regenerate)"""
    item = db.query(ContentReviewItem).filter(ContentReviewItem.id == item_id).first()
    if not item or item.campaign_id != campaign_id:
        raise HTTPException(status_code=404, detail="Review item not found")

    item.status = action
    item.reviewed_at = datetime.utcnow()
    if notes:
        item.review_notes = notes

    db.commit()
    return {"status": "updated"}

# Advanced Settings
@router.get("/campaigns/{campaign_id}/advanced-settings")
def get_advanced_settings(campaign_id: int, db: Session = Depends(get_db)):
    """Get advanced settings for a campaign"""
    settings = db.query(CampaignAdvancedSettings).filter(
        CampaignAdvancedSettings.campaign_id == campaign_id
    ).first()

    if settings:
        return {
            "max_posts_per_subreddit_week": settings.max_posts_per_subreddit_week,
            "min_hours_between_posts": settings.min_hours_between_posts,
            "min_uniqueness_score": settings.min_uniqueness_score,
            "min_relevance_score": settings.min_relevance_score,
            "require_manual_approval": settings.require_manual_approval,
            "avoid_similar_titles": settings.avoid_similar_titles,
            "rotate_personas_evenly": settings.rotate_personas_evenly,
            "balance_keyword_themes": settings.balance_keyword_themes
        }
    else:
        # Return defaults
        return {
            "max_posts_per_subreddit_week": 2,
            "min_hours_between_posts": 24,
            "min_uniqueness_score": 70,
            "min_relevance_score": 80,
            "require_manual_approval": "never",
            "avoid_similar_titles": True,
            "rotate_personas_evenly": True,
            "balance_keyword_themes": True
        }

@router.put("/campaigns/{campaign_id}/advanced-settings")
def update_advanced_settings(
    campaign_id: int,
    settings: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Update advanced settings for a campaign"""
    existing = db.query(CampaignAdvancedSettings).filter(
        CampaignAdvancedSettings.campaign_id == campaign_id
    ).first()

    if existing:
        # Update existing
        for key, value in settings.items():
            if hasattr(existing, key):
                setattr(existing, key, value)
    else:
        # Create new
        new_settings = CampaignAdvancedSettings(campaign_id=campaign_id, **settings)
        db.add(new_settings)

    db.commit()
    return {"status": "updated"}
