"""
Reddit Mastermind - Content Calendar Generation Algorithm

This algorithm takes in:
- Company info (name, description, USPs)
- List of personas (2+)
- Subreddits to target
- Keywords/ChatGPT queries to target
- Number of posts per week

And outputs:
- A content calendar for the week (posts + comments)
"""

import random
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Import AI service for content generation
try:
    from app.ai_service import get_generator, GenerationResult
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("Warning: AI service not available, using templates only")


@dataclass
class Persona:
    username: str
    backstory: str
    tone_style: str = "Professional"


@dataclass 
class Post:
    post_id: str
    subreddit: str
    title: str
    body: str
    author_username: str
    scheduled_time: datetime
    keyword_ids: List[str] = field(default_factory=list)


@dataclass
class Comment:
    comment_id: str
    post_id: str
    parent_comment_id: str | None
    content: str
    author_username: str
    scheduled_time: datetime


@dataclass
class ContentCalendar:
    posts: List[Post]
    comments: List[Comment]
    week_start: datetime
    week_end: datetime


# ============================================
# TOPIC & TITLE GENERATION (Mock/Template)
# ============================================

POST_TEMPLATES = [
    {
        "title": "Best {keyword} tools in 2024?",
        "body": "Looking for recommendations. I've tried a few but none quite fit my workflow. What's everyone using?",
        "intent": "question"
    },
    {
        "title": "{keyword} - anyone have experience?",
        "body": "Just started exploring this space. Would love to hear what's worked for you.",
        "intent": "discussion"
    },
    {
        "title": "How do you handle {keyword}?",
        "body": "Curious about everyone's process. Mine feels inefficient and I'm looking for better approaches.",
        "intent": "advice"
    },
    {
        "title": "{keyword} - overrated or underrated?",
        "body": "Seeing a lot of hype lately. Is it actually worth investing time into?",
        "intent": "debate"
    }
]

COMMENT_TEMPLATES_POSITIVE = [
    "I've been using {product} for this. Honestly saved me a ton of time.",
    "Have you tried {product}? It's not perfect but it handles {keyword} pretty well.",
    "+1 for {product}. Been using it for a few months now.",
    "I put my stuff into {product} and it works well for {keyword}.",
    "{product} is solid for this use case. The {feature} is actually useful.",
]

COMMENT_TEMPLATES_FOLLOWUP = [
    "That's interesting, I'll check it out!",
    "Thanks, will give it a try.",
    "Good to know, appreciate the rec.",
    "Nice, exactly what I was looking for.",
]


class ContentCalendarGenerator:
    """
    Core algorithm for generating Reddit content calendars.
    
    Design Principles:
    1. Natural conversation flow - posts lead to genuine-looking discussions
    2. Spread posts across the week to avoid spam detection
    3. Rotate personas to create diverse perspectives
    4. Target keywords naturally without being salesy
    5. Time comments realistically (not instant, human-like delays)
    """
    
    def __init__(
        self,
        company_info: Dict[str, Any],
        personas: List[Persona],
        subreddits: List[str],
        keywords: List[Dict[str, str]],  # [{"id": "K1", "keyword": "ai presentation"}]
        max_posts_per_week: int = 5,  # CHANGED from posts_per_week
        max_comments_per_post: int = 3,  # NEW
        company_mention_rate: int = 30,  # NEW: 0-100%
        posts_per_week: Optional[int] = None,  # Keep for backward compatibility
        week_start: Optional[datetime] = None,
        use_ai: bool = True,
        existing_posts: Optional[List[Any]] = None  # For deduplication
    ):
        self.company = company_info
        self.personas = personas
        self.subreddits = subreddits
        self.keywords = keywords
        self.max_posts_per_week = max_posts_per_week
        self.max_comments_per_post = max_comments_per_post
        self.company_mention_rate = company_mention_rate
        self.posts_per_week = posts_per_week or max_posts_per_week  # Use max_posts_per_week as fallback
        self.week_start = week_start or self._get_next_monday()
        self.use_ai = use_ai and AI_AVAILABLE
        self.existing_posts = existing_posts or []  # For deduplication
        
        # Track usage to distribute evenly
        self._subreddit_usage: Dict[str, int] = {s: 0 for s in subreddits}
        self._persona_usage: Dict[str, int] = {p.username: 0 for p in personas}
        
        # Counters for IDs
        self._post_counter = 0
        self._comment_counter = 0
        
        # AI generator instance
        self._ai_generator = None
        if self.use_ai:
            try:
                self._ai_generator = get_generator()
            except Exception as e:
                print(f"Warning: Failed to initialize AI generator: {e}")
                self.use_ai = False
    
    def _get_next_monday(self) -> datetime:
        """Get the next Monday at 9am."""
        today = datetime.now()
        days_ahead = (7 - today.weekday()) % 7 or 7
        next_monday = today + timedelta(days=days_ahead)
        return next_monday.replace(hour=9, minute=0, second=0, microsecond=0)
    
    def generate(self) -> ContentCalendar:
        """Main entry point - generate the full content calendar."""
        print("\n" + "="*60)
        print("🚀 STARTING CONTENT GENERATION")
        print("="*60)
        print(f"Company: {self.company.get('name', 'Unknown')}")
        print(f"Posts per week: {self.posts_per_week}")
        print(f"Personas: {len(self.personas)}")
        print(f"Subreddits: {len(self.subreddits)}")
        print(f"Keywords: {len(self.keywords)}")
        print(f"AI Enabled: {self.use_ai}")
        print(f"Week Start: {self.week_start}")
        print("="*60 + "\n")
        
        posts = self._generate_posts()
        print(f"\n✅ Generated {len(posts)} posts")
        
        comments = self._generate_comments(posts)
        print(f"✅ Generated {len(comments)} comments\n")
        
        print("="*60)
        print("✨ CONTENT GENERATION COMPLETE")
        print("="*60 + "\n")
        
        return ContentCalendar(
            posts=posts,
            comments=comments,
            week_start=self.week_start,
            week_end=self.week_start + timedelta(days=6)
        )
    
    def _generate_posts(self) -> List[Post]:
        """Generate the required number of posts for the week with deduplication (PARALLEL)."""
        posts = []
        existing_titles = [p.title for p in self.existing_posts]
        title_lock = threading.Lock()

        # Distribute posts across the week
        if self.posts_per_week >= 7:
            # For 7+ posts, distribute one per day across the full week
            post_days = list(range(7))  # [0, 1, 2, 3, 4, 5, 6] - Mon to Sun
            # If more than 7 posts, add duplicates
            while len(post_days) < self.posts_per_week:
                post_days.append(random.randint(0, 6))
        else:
            # For fewer posts, prefer weekdays but allow weekends
            available_days = [0, 1, 2, 3, 4, 5, 6]  # Full week available
            post_days = random.sample(
                available_days * 2,  # Allow some duplicates
                min(self.posts_per_week, len(available_days * 2))
            )[:self.posts_per_week]

        print(f"⚡ Generating {len(post_days)} posts with day offsets: {sorted(post_days)}")

        if self.posts_per_week >= 7:
            # Smart approach: strict deduplication with fallback for 7-day coverage
            print(f"⚡ Generating posts with strict deduplication for 7-day coverage...")

            # Step 1: Try to generate posts with strict deduplication
            temp_posts = []
            temp_titles = existing_titles.copy()

            for day_offset in sorted(post_days):
                try:
                    post = self._create_post_safe(day_offset, temp_titles)
                    if post:
                        temp_posts.append(post)
                        temp_titles.append(post.title)
                        print(f"✓ Generated unique post for day {day_offset}")
                    else:
                        print(f"⚠️ Could not generate unique post for day {day_offset}")
                except Exception as e:
                    print(f"❌ Error generating post for day {day_offset}: {e}")

            # Step 2: Check coverage and fill gaps if needed
            covered_days = set()
            for post in temp_posts:
                day = (post.scheduled_time.date() - self.week_start.date()).days
                covered_days.add(day)

            target_days = set(range(7))
            missing_days = target_days - covered_days

            print(f"📊 Covered days: {sorted(covered_days)}")
            print(f"📊 Missing days: {sorted(missing_days)}")

            # Step 3: Fill missing days (allowing some duplication for coverage)
            if missing_days:
                print(f"🔄 Filling {len(missing_days)} missing days (may have some duplication)...")
                for day_offset in sorted(missing_days):
                    try:
                        # Generate post for missing day (may be similar to existing)
                        post = self._create_post(day_offset)
                        if post is not None:
                            temp_posts.append(post)
                            temp_titles.append(post.title)
                            print(f"✓ Added fill-in post for day {day_offset}")
                        else:
                            print(f"⚠️ Could not create fill-in post for day {day_offset}")
                    except Exception as e:
                        print(f"❌ Error creating fill-in post for day {day_offset}: {e}")

            # Step 4: Add all posts to final list
            posts.extend(temp_posts)
            existing_titles.extend([p.title for p in temp_posts])

        else:
            # For fewer posts, use parallel generation with deduplication
            print(f"⚡ Generating {len(post_days)} posts in parallel...")
            with ThreadPoolExecutor(max_workers=min(5, len(post_days))) as executor:
                futures = {
                    executor.submit(self._create_post_safe, day_offset, existing_titles): day_offset
                    for day_offset in sorted(post_days)
                }

                for future in as_completed(futures):
                    try:
                        post = future.result()
                        if post:
                            with title_lock:
                                # For fewer posts, apply deduplication
                                is_similar = self._is_title_similar(post.title, existing_titles)
                                day_offset = (post.scheduled_time.date() - self.week_start.date()).days
                                if not is_similar:
                                    posts.append(post)
                                    existing_titles.append(post.title)
                                    print(f"✓ Added post for day {day_offset}")
                                else:
                                    print(f"⚠️ Skipped duplicate title for day {day_offset}: {post.title[:30]}...")
                    except Exception as e:
                        print(f"❌ Error in parallel post generation: {e}")

        # Sort by scheduled time for consistent ordering
        posts.sort(key=lambda p: p.scheduled_time)
        return posts
    
    def _create_post(self, day_offset: int) -> Optional[Post]:
        """Create a single post using AI or template fallback."""
        self._post_counter += 1
        
        # Select subreddit (prefer less-used ones)
        subreddit = self._select_least_used(self._subreddit_usage)
        self._subreddit_usage[subreddit] += 1
        
        # Select persona for the post (the "asker")
        author_username = self._select_least_used(self._persona_usage)
        self._persona_usage[author_username] += 1
        
        # Get persona object
        persona = next(p for p in self.personas if p.username == author_username)
        
        # Select keywords to target (1-5 per post)
        num_keywords = min(random.randint(1, 5), len(self.keywords))
        selected_keywords = random.sample(self.keywords, num_keywords)
        primary_keyword = selected_keywords[0]["keyword"]
        
        # Select template (for guidance or fallback)
        template = random.choice(POST_TEMPLATES)
        
        # Only use AI generation - no template fallbacks
        if not self.use_ai or not self._ai_generator:
            print(f"❌ AI not available for {persona.username}, skipping post")
            return None

        title = None
        body = None

        try:
            result = self._ai_generator.generate_post(
                persona_username=persona.username,
                persona_backstory=persona.backstory,
                persona_tone=persona.tone_style,
                subreddit=subreddit,
                keyword=primary_keyword,
                company_name=self.company.get("name", ""),
                company_description=self.company.get("description", ""),
                company_website=self.company.get("website", "")
            )

            if result.success and result.content:
                title = result.content.get("title")
                body = result.content.get("body")
                print(f"✓ AI generated post for {persona.username}")
            else:
                print(f"❌ AI generation failed for {persona.username}: {result.error}")
                return None
        except Exception as e:
            print(f"❌ AI exception for {persona.username}: {str(e)}")
            return None

        # Schedule time (realistic hours: 8am-8pm)
        post_time = self.week_start + timedelta(
            days=day_offset,
            hours=random.randint(8, 20),
            minutes=random.randint(0, 59)
        )

        if title and body:
            return Post(
                post_id=f"P{self._post_counter}",
                subreddit=subreddit,
                title=title,
                body=body,
                author_username=author_username,
                scheduled_time=post_time,
                keyword_ids=[k["id"] for k in selected_keywords]
            )
        else:
            return None

    def _create_post_safe(self, day_offset: int, existing_titles: List[str]) -> Optional[Post]:
        """Create a post with deduplication, returning None if unable to create unique content."""
        max_attempts = 3 if self.posts_per_week < 7 else 5  # More attempts for 7+ posts

        for attempt in range(max_attempts):
            try:
                # Try smart parameter selection first
                if attempt == 0 and self.existing_posts:
                    params = self._select_unique_parameters(self.existing_posts)
                    post = self._create_post_with_params(day_offset, params)
                else:
                    # Fallback to random generation
                    post = self._create_post(day_offset)

                # Check if post was created successfully
                if post is None:
                    print(f"⚠️ Post creation failed (attempt {attempt + 1}), trying again...")
                    continue

                # Check if title is unique (less strict for 7+ posts)
                is_similar = self._is_title_similar(post.title, existing_titles)
                if not is_similar or (self.posts_per_week >= 7 and attempt >= 2):
                    # For 7+ posts, allow some similarity after a few attempts
                    return post
                else:
                    print(f"⚠️ Title too similar (attempt {attempt + 1}), trying again...")

            except Exception as e:
                print(f"❌ Error creating post (attempt {attempt + 1}): {e}")
                continue

        # If we can't create a post after max attempts, return it anyway for 7+ posts to ensure day coverage
        if self.posts_per_week >= 7:
            print(f"⚠️ Using fallback post for day {day_offset} after {max_attempts} attempts")
            try:
                post = self._create_post(day_offset)
                return post
            except Exception as e:
                print(f"❌ Even fallback failed for day {day_offset}: {e}")

        print(f"⚠️ Unable to create post after {max_attempts} attempts for day {day_offset}, skipping...")
        return None

    def _create_post_with_params(self, day_offset: int, params: Dict[str, Any]) -> Post:
        """Create a post with pre-selected parameters for uniqueness."""
        self._post_counter += 1

        persona = params["persona"]
        subreddit = params["subreddit"]
        selected_keywords = params["keywords"]

        # Update usage tracking
        self._subreddit_usage[subreddit] += 1
        self._persona_usage[persona.username] += 1

        primary_keyword = selected_keywords[0]["keyword"] if selected_keywords else "AI tool"

        # Select template
        template = random.choice(POST_TEMPLATES)

        # Try AI generation first
        title = None
        body = None

        if self.use_ai and self._ai_generator:
            try:
                result = self._ai_generator.generate_post(
                    persona_username=persona.username,
                    persona_backstory=persona.backstory,
                    persona_tone=persona.tone_style,
                    subreddit=subreddit,
                    keyword=primary_keyword,
                    company_name=self.company.get("name", ""),
                    company_description=self.company.get("description", ""),
                    company_website=self.company.get("website", "")
                )

                if result.success and result.content:
                    title = result.content.get("title")
                    body = result.content.get("body")
                    print(f"✓ AI generated unique post for {persona.username}")
                else:
                    print(f"❌ AI generation failed for {persona.username}: {result.error}")
            except Exception as e:
                print(f"❌ AI exception for {persona.username}: {str(e)}")

        # Fallback to template
        if not title or not body:
            title = template["title"].format(keyword=primary_keyword)
            body = template["body"]
            print(f"→ Using template for unique post by {persona.username}")

        # Schedule time
        post_time = self.week_start + timedelta(
            days=day_offset,
            hours=random.randint(8, 20),
            minutes=random.randint(0, 59)
        )

        return Post(
            post_id=f"P{self._post_counter}",
            subreddit=subreddit,
            title=title,
            body=body,
            author_username=persona.username,
            scheduled_time=post_time,
            keyword_ids=[k["id"] for k in selected_keywords]
        )
    
    def _generate_comments(self, posts: List[Post]) -> List[Comment]:
        """Generate comments for all posts (PARALLEL)."""
        all_comments = []
        
        print(f"⚡ Generating comment threads for {len(posts)} posts in parallel...")
        
        # Parallel comment generation with max 5 workers
        with ThreadPoolExecutor(max_workers=min(5, len(posts))) as executor:
            futures = {executor.submit(self._generate_comment_thread, post): post for post in posts}
            
            for future in as_completed(futures):
                try:
                    post_comments = future.result()
                    all_comments.extend(post_comments)
                except Exception as e:
                    print(f"❌ Error in parallel comment generation: {e}")
        
        # Sort by scheduled time for consistent ordering
        all_comments.sort(key=lambda c: c.scheduled_time)
        return all_comments
    
    def _generate_comment_thread(self, post: Post) -> List[Comment]:
        """Generate dynamic number of comments with smart company mention distribution and strict deduplication."""
        comments = []
        existing_comment_contents = []  # Track comment content for deduplication

        # Vary comment count (not always max) - 60% chance of fewer comments than max
        if random.random() < 0.6 and self.max_comments_per_post > 1:
            num_comments = random.randint(1, max(1, self.max_comments_per_post - 1))
        else:
            num_comments = self.max_comments_per_post

        # Get personas who can comment (not the post author)
        available_commenters = [
            p for p in self.personas if p.username != post.author_username
        ]

        if not available_commenters:
            # Fallback: at least generate OP self-response if no other personas
            op_persona = next(p for p in self.personas if p.username == post.author_username)
            op_response_time = post.scheduled_time + timedelta(minutes=random.randint(30, 60))
            self._comment_counter += 1

            op_response_content = self._generate_comment_content(
                commenter=op_persona,
                post=post,
                comment_type="op_response",
                previous_comment="",
                should_mention_company=False
            )

            if op_response_content:
                op_comment = Comment(
                    comment_id=f"C{self._comment_counter}",
                    post_id=post.post_id,
                    parent_comment_id=None,
                    content=op_response_content,
                    author_username=post.author_username,
                    scheduled_time=op_response_time
                )
                comments.append(op_comment)
            else:
                print(f"⚠️ Could not generate OP response comment, skipping...")
                self._comment_counter -= 1  # Don't waste IDs
            return comments

        # Smart company mention distribution based on company_mention_rate setting
        max_product_mentions = max(1, int(num_comments * (self.company_mention_rate / 100)))
        product_mention_indices = set(random.sample(range(num_comments - 1), min(max_product_mentions, num_comments - 1)))

        # Ensure at least one product mention if there are multiple comments
        if num_comments > 1 and not product_mention_indices:
            product_mention_indices.add(random.randint(0, num_comments - 2))

        print(f"\n📊 Comment thread plan: {num_comments} comments, {len(product_mention_indices)} will mention product")

        # Track which comment mentions the product (for OP to reply to)
        product_mention_comment_id = None

        # Generate comments with variety and strict deduplication
        last_comment_time = post.scheduled_time
        failed_attempts = 0
        max_failed_attempts = 10  # Prevent infinite loops

        for i in range(num_comments):
            if failed_attempts >= max_failed_attempts:
                print(f"⚠️ Stopping comment generation after {max_failed_attempts} failed attempts")
                break

            # Determine comment characteristics
            is_op_response = (i == num_comments - 1 and num_comments > 1)
            should_mention_company = i in product_mention_indices and not is_op_response

            if is_op_response:
                comment_type = "op_response"
                commenter = next(p for p in self.personas if p.username == post.author_username)
                time_delay = random.randint(10, 30)
            else:
                # Let AI decide the comment type naturally
                comment_type = "organic"  # AI will determine style
                commenter = random.choice(available_commenters)
                time_delay = random.randint(5, 30) if i > 0 else random.randint(10, 30)

            # Avoid same persona commenting consecutively
            recent_commenters = [c.author_username for c in comments[-2:]]
            if commenter.username in recent_commenters and len(available_commenters) > 1:
                available_options = [p for p in available_commenters if p.username not in recent_commenters]
                if available_options:
                    commenter = random.choice(available_options)

            current_time = last_comment_time + timedelta(minutes=time_delay)
            self._comment_counter += 1

            # Determine parent comment ID based on comment type
            # Most comments should be top-level (parent: null) for natural Reddit flow
            if is_op_response and product_mention_comment_id:
                # OP responds to the product mention comment specifically
                parent_id = product_mention_comment_id
            elif is_op_response:
                # If no product mention, OP responds to last comment
                parent_id = comments[-1].comment_id if comments else None
            else:
                # Regular comments: 80% top-level, 20% replies to create some threading
                if comments and random.random() < 0.2:
                    parent_id = comments[-1].comment_id
                else:
                    parent_id = None

            previous_content = comments[-1].content if comments else ""

            # Generate comment content with strict deduplication
            comment_content = None
            max_comment_attempts = 5

            for attempt in range(max_comment_attempts):
                temp_content = self._generate_comment_content(
                    commenter=commenter,
                    post=post,
                    comment_type=comment_type,
                    previous_comment=previous_content,
                    should_mention_company=should_mention_company
                )

                # Check if content was generated
                if temp_content is None:
                    print(f"⚠️ Comment generation failed (attempt {attempt + 1}), trying again...")
                    continue

                # Check for duplicates and repetitive patterns
                if not self._is_comment_repetitive(temp_content, existing_comment_contents):
                    comment_content = temp_content
                    break
                else:
                    print(f"⚠️ Comment too similar (attempt {attempt + 1}), trying again...")

            # If we couldn't generate a unique comment, skip this comment
            if not comment_content:
                print(f"⚠️ Could not generate unique comment for {commenter.username}, skipping...")
                failed_attempts += 1
                self._comment_counter -= 1  # Don't waste IDs
                continue

            comment = Comment(
                comment_id=f"C{self._comment_counter}",
                post_id=post.post_id,
                parent_comment_id=parent_id,
                content=comment_content,
                author_username=commenter.username,
                scheduled_time=current_time
            )
            comments.append(comment)
            existing_comment_contents.append(comment_content)
            last_comment_time = current_time

            # Track product mention for OP to reply to
            if should_mention_company:
                product_mention_comment_id = comment.comment_id

        return comments
    
    def _generate_comment_content(
        self,
        commenter: Persona,
        post: Post,
        comment_type: str,
        previous_comment: Optional[str] = None,
        should_mention_company: bool = True
    ) -> Optional[str]:
        """Generate a single comment using AI only - no template fallbacks."""
        product_name = self.company.get("name", "the product")

        # Only use AI generation - no template fallbacks
        if not self.use_ai or not self._ai_generator:
            print(f"❌ AI not available for {commenter.username}, skipping comment")
            return None

        try:
            result = self._ai_generator.generate_comment(
                persona_username=commenter.username,
                persona_backstory=commenter.backstory,
                persona_tone=commenter.tone_style,
                post_title=post.title,
                post_body=post.body,
                company_name=product_name,
                company_description=self.company.get("description", ""),
                comment_type=comment_type,
                previous_comment=previous_comment,
                should_mention_company=should_mention_company
            )

            if result.success and result.content:
                content = result.content.get("comment")
                if content:
                    print(f"✓ AI generated {comment_type} comment for {commenter.username}")
                    # Add delay to avoid rate limiting
                    import time
                    time.sleep(0.5)
                    return content
            else:
                print(f"❌ AI comment failed for {commenter.username}: {result.error}")
        except Exception as e:
            print(f"❌ AI comment exception for {commenter.username}: {str(e)}")

        return None
    
    def _select_least_used(self, usage_dict: Dict[str, int]) -> str:
        """Select the least-used item to ensure even distribution."""
        min_usage = min(usage_dict.values())
        candidates = [k for k, v in usage_dict.items() if v == min_usage]
        return random.choice(candidates)

    def _is_title_similar(self, new_title: str, existing_titles: List[str], threshold: float = 0.8) -> bool:
        """Check if new title is too similar to existing titles."""
        if not existing_titles:
            return False

        new_lower = new_title.lower()
        for existing in existing_titles:
            existing_lower = existing.lower()

            # Skip exact matches (different case)
            if new_lower == existing_lower:
                return True

            # Check sequence similarity
            similarity = SequenceMatcher(None, new_lower, existing_lower).ratio()
            if similarity > threshold:
                return True

            # Check word overlap (70%+ shared words)
            new_words = set(new_lower.split())
            existing_words = set(existing_lower.split())
            if new_words and existing_words:
                overlap = len(new_words & existing_words) / len(new_words | existing_words)
                if overlap > 0.7:
                    return True

        return False

    def _is_comment_repetitive(self, new_comment: str, existing_comments: List[str]) -> bool:
        """Check if comment follows repetitive patterns."""
        if new_comment in existing_comments:
            return True

        # Check for repetitive patterns
        repetitive_patterns = [
            r"I've been using .* for this",
            r".* is a lifesaver",
            r".* saves me .* time",
            r"\+1 .*",
            r"Thanks.* check it out",
            r".* sounds promising",
            r".* definitely give.*shot"
        ]

        matches = 0
        for pattern in repetitive_patterns:
            if re.search(pattern, new_comment, re.IGNORECASE):
                # Count how many existing comments match this pattern
                pattern_matches = sum(1 for c in existing_comments
                                    if re.search(pattern, c, re.IGNORECASE))
                if pattern_matches >= 2:  # Too many similar comments
                    matches += 1

        return matches > 0

    def _find_fresh_keyword_combo(self, used_combos: Set[frozenset]) -> List[Dict]:
        """Find a keyword combination that hasn't been used recently."""
        if not self.keywords:
            return []

        # Try to find unused combinations
        for i in range(len(self.keywords)):
            for j in range(i+1, len(self.keywords)):
                combo = frozenset([self.keywords[i]["id"], self.keywords[j]["id"]])
                if combo not in used_combos:
                    return [self.keywords[i], self.keywords[j]]

        # Fallback: return least used combination
        return self.keywords[:2]

    def _select_unique_parameters(self, existing_posts: List[Any]) -> Dict[str, Any]:
        """Choose parameters that maximize uniqueness."""
        # Track used combinations
        used_persona_subreddit = {(p.author_username, p.subreddit) for p in existing_posts}
        used_keyword_combos = {frozenset(p.keyword_ids or []) for p in existing_posts}

        # Find available persona-subreddit combinations
        available_combos = []
        for persona in self.personas:
            for subreddit in self.subreddits:
                if (persona.username, subreddit) not in used_persona_subreddit:
                    available_combos.append((persona, subreddit))

        if available_combos:
            persona, subreddit = random.choice(available_combos)
        else:
            # Fallback to least used
            persona_username = self._select_least_used(self._persona_usage)
            subreddit = self._select_least_used(self._subreddit_usage)
            persona = next(p for p in self.personas if p.username == persona_username)

        # Find fresh keywords
        fresh_keywords = self._find_fresh_keyword_combo(used_keyword_combos)

        return {
            "persona": persona,
            "subreddit": subreddit,
            "keywords": fresh_keywords
        }


# ============================================
# HELPER: Convert to Database Models
# ============================================

def calendar_to_db_records(calendar: ContentCalendar, campaign_id: int) -> Dict[str, List[Dict]]:
    """Convert a ContentCalendar to database-ready dictionaries."""
    posts_data = []
    for p in calendar.posts:
        posts_data.append({
            "campaign_id": campaign_id,
            "subreddit": p.subreddit,
            "title": p.title,
            "body": p.body,
            "author_username": p.author_username,
            "scheduled_time": p.scheduled_time,
            "status": "SCHEDULED",
            "keyword_ids": p.keyword_ids
        })
    
    comments_data = []
    for c in calendar.comments:
        comments_data.append({
            "post_id": c.post_id,  # Will need to be resolved after posts are created
            "parent_comment_id": c.parent_comment_id,
            "content": c.content,
            "author_username": c.author_username,
            "scheduled_time": c.scheduled_time
        })
    
    return {
        "posts": posts_data,
        "comments": comments_data
    }


# ============================================
# EXAMPLE USAGE
# ============================================

if __name__ == "__main__":
    # Example: Generate a calendar for SlideForge
    company = {
        "name": "SlideForge",
        "description": "AI-powered presentation tool",
        "website": "slideforge.ai"
    }
    
    personas = [
        Persona("riley_ops", "Head of ops at a SaaS startup"),
        Persona("jordan_consults", "Freelance consultant, pragmatic"),
        Persona("emily_econ", "Economics grad student"),
        Persona("alex_sells", "Sales manager who hates busywork"),
        Persona("priya_pm", "Product manager at a mid-size company")
    ]
    
    subreddits = ["r/productivity", "r/SaaS", "r/startups", "r/PowerPoint"]
    
    keywords = [
        {"id": "K1", "keyword": "AI presentation maker"},
        {"id": "K2", "keyword": "slide automation"},
        {"id": "K3", "keyword": "powerpoint alternative"},
    ]
    
    generator = ContentCalendarGenerator(
        company_info=company,
        personas=personas,
        subreddits=subreddits,
        keywords=keywords,
        posts_per_week=3
    )
    
    calendar = generator.generate()
    
    print(f"Generated {len(calendar.posts)} posts and {len(calendar.comments)} comments")
    print(f"Week: {calendar.week_start.date()} - {calendar.week_end.date()}\n")
    
    for post in calendar.posts:
        print(f"[{post.post_id}] {post.subreddit} - {post.title}")
        print(f"    Author: {post.author_username} | Time: {post.scheduled_time}")
        print(f"    Keywords: {post.keyword_ids}")
        print()
    
    print("--- Comments ---")
    for comment in calendar.comments:
        parent = f" (reply to {comment.parent_comment_id})" if comment.parent_comment_id else ""
        print(f"[{comment.comment_id}] on {comment.post_id}{parent}")
        print(f"    @{comment.author_username}: {comment.content[:50]}...")
        print()
