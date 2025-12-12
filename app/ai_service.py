"""
AI Content Generation Service using Google Gemini

This module handles all AI-powered content generation for Reddit posts and comments.
Uses Gemini Flash for cost-effective, high-quality content generation.
"""

import os
import json
import time
from typing import Dict, List, Optional, Tuple
import google.generativeai as genai
from dataclasses import dataclass


@dataclass
class GenerationResult:
    """Result of an AI generation attempt"""
    success: bool
    content: Optional[Dict] = None
    error: Optional[str] = None
    tokens_used: int = 0
    retry_count: int = 0


class GeminiContentGenerator:
    """
    Handles AI content generation using Google Gemini API.
    
    Features:
    - Post generation (titles + bodies)
    - Comment generation (various types)
    - Quality validation
    - Cost tracking
    - Retry logic
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Gemini API key (defaults to env var GEMINI_API_KEY)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Use Gemini Flash for cost optimization
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Generation config for cost control
        self.generation_config = {
            "temperature": 0.9,  # High creativity for natural variation
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 2000,  # Increased for complete responses
        }
        
        # Safety settings (allow most content for Reddit authenticity)
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
        ]
        
        # Track usage for cost monitoring
        self.total_tokens_used = 0
    
    def generate_post(
        self,
        persona_username: str,
        persona_backstory: str,
        persona_tone: str,
        subreddit: str,
        keyword: str,
        company_name: str,
        company_description: str = "",
        company_website: str = "",
        template: Optional[Dict[str, str]] = None,
        max_retries: int = 3
    ) -> GenerationResult:
        """
        Generate a Reddit post (title + body).
        
        Args:
            persona_username: Username of the posting persona
            persona_backstory: Full backstory of the persona
            persona_tone: Tone style (e.g., "Professional", "Casual")
            subreddit: Target subreddit (e.g., "r/ProductManagement")
            keyword: Keyword to target (e.g., "AI presentation maker")
            company_name: Company name (should NOT appear in post)
            company_description: What the company does
            company_website: Company website
            max_retries: Maximum retry attempts if generation fails
        
        Returns:
            GenerationResult with post data or error
        """
        prompt = self._build_post_prompt(
            persona_username,
            persona_backstory,
            persona_tone,
            subreddit,
            keyword,
            company_name,
            company_description,
            company_website,
            template
        )
        
        for attempt in range(max_retries):
            try:
                print(f"\n🤖 AI Attempt {attempt + 1}/{max_retries} for post generation...")
                response = self.model.generate_content(
                    prompt,
                    generation_config=self.generation_config,
                    safety_settings=self.safety_settings
                )
                
                # Extract content
                content_text = response.text.strip()
                print(f"📝 Raw Gemini response ({len(content_text)} chars):")
                print(f"   {content_text[:200]}...")
                
                # Parse JSON response
                post_data = self._parse_post_json(content_text)
                
                if not post_data:
                    print(f"   ❌ JSON parsing failed")
                    continue  # Retry if parsing failed
                
                print(f"   ✓ JSON parsed successfully")
                
                # Validate quality
                if self._validate_post_quality(post_data, company_name):
                    # Estimate tokens (rough approximation)
                    tokens = len(prompt) // 4 + len(content_text) // 4
                    self.total_tokens_used += tokens
                    
                    return GenerationResult(
                        success=True,
                        content=post_data,
                        tokens_used=tokens,
                        retry_count=attempt
                    )
            
            except Exception as e:
                if attempt == max_retries - 1:
                    return GenerationResult(
                        success=False,
                        error=f"Failed after {max_retries} attempts: {str(e)}",
                        retry_count=attempt
                    )
                time.sleep(1)  # Brief delay before retry
        
        return GenerationResult(
            success=False,
            error="Failed to generate valid post",
            retry_count=max_retries
        )
    
    def generate_comment(
        self,
        persona_username: str,
        persona_backstory: str,
        persona_tone: str,
        post_title: str,
        post_body: str,
        company_name: str,
        company_description: str = "",
        comment_type: str = "product_mention",
        previous_comment: Optional[str] = None,
        should_mention_company: bool = True,
        max_retries: int = 3
    ) -> GenerationResult:
        """
        Generate a Reddit comment.
        
        Args:
            persona_username: Username of commenting persona
            persona_backstory: Full backstory of the persona
            persona_tone: Tone style
            post_title: Title of the post being commented on
            post_body: Body of the post being commented on
            company_name: Company name to mention (if product_mention type)
            company_description: What the company does
            comment_type: Type of comment ("product_mention", "validation", "op_response")
            previous_comment: Previous comment in thread (for context)
            max_retries: Maximum retry attempts
        
        Returns:
            GenerationResult with comment text or error
        """
        prompt = self._build_comment_prompt(
            persona_username,
            persona_backstory,
            persona_tone,
            post_title,
            post_body,
            company_name,
            company_description,
            comment_type,
            previous_comment,
            should_mention_company
        )
        
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config=self.generation_config,
                    safety_settings=self.safety_settings
                )
                
                comment_text = response.text.strip()
                
                # Remove any markdown formatting or quotes
                comment_text = comment_text.strip('"').strip("'")
                
                # Validate quality
                if self._validate_comment_quality(comment_text, comment_type, company_name):
                    tokens = len(prompt) // 4 + len(comment_text) // 4
                    self.total_tokens_used += tokens
                    
                    return GenerationResult(
                        success=True,
                        content={"comment": comment_text},
                        tokens_used=tokens,
                        retry_count=attempt
                    )
            
            except Exception as e:
                if attempt == max_retries - 1:
                    return GenerationResult(
                        success=False,
                        error=f"Failed after {max_retries} attempts: {str(e)}",
                        retry_count=attempt
                    )
                time.sleep(1)
        
        return GenerationResult(
            success=False,
            error="Failed to generate valid comment",
            retry_count=max_retries
        )
    
    def _build_post_prompt(
        self,
        username: str,
        backstory: str,
        tone: str,
        subreddit: str,
        keyword: str,
        company_name: str,
        company_description: str,
        company_website: str,
        template: Optional[Dict[str, str]] = None
    ) -> str:
        """Build prompt for post generation with optional template guidance"""
        
        # Build company context
        company_context = f"\n\nContext (for your knowledge, don't mention in post):"
        if company_description:
            company_context += f"\n- There's a product called {company_name} that {company_description}"
        if company_website:
            company_context += f"\n- Website: {company_website}"
        company_context += f"\n- Your post should ask about problems that {company_name} solves (based on keyword: '{keyword}')"
        company_context += f"\n- But DON'T mention {company_name} in your post - you're asking for solutions, not promoting"
        
        # Base prompt
        base_prompt = f"""You are {username}, a Reddit user.

Your background:
{backstory}

Your tone style: {tone}

Task: Write an authentic Reddit post for {subreddit} that would naturally appear when someone searches for: "{keyword}"

Your post should address this exact question/problem that people are searching for.{company_context}"""
        
        # Add template guidance if provided
        if template:
            template_guidance = f"""

Here's an example style to inspire you (don't copy exactly, make it YOUR voice):
Intent: {template.get('intent', 'question')}
Example title format: {template.get('title', '')}
Example body tone: {template.get('body', '')}

Use this as inspiration but make it sound like YOU based on your background."""
        else:
            template_guidance = ""
        
        # Requirements
        requirements = """

Requirements:
- Write in first person as this character
- Include specific details from your background that make this authentic
- Sound natural and conversational, not robotic or templated
- Address the EXACT search query/question: "{keyword}"
- Your post should match what someone searching for this would want to read
- Be curious and specific about what you need help with
- Do NOT mention "{company_name}" in the post (you're asking for help, not promoting)
- Do NOT use em-dashes (—) or fancy punctuation - use regular hyphens (-) or commas instead
- Keep the post concise but engaging (50-150 words for body)

Return your response as valid JSON in this exact format:
{{
  "title": "Your post title here",
  "body": "Your post body here"
}}

Remember: You're a real person with a real problem seeking genuine advice. Your post should naturally rank for the search query above."""
        
        return base_prompt + template_guidance + requirements.format(company_name=company_name, keyword=keyword)
    
    def _build_comment_prompt(
        self,
        username: str,
        backstory: str,
        tone: str,
        post_title: str,
        post_body: str,
        company_name: str,
        company_description: str,
        comment_type: str,
        previous_comment: Optional[str],
        should_mention_company: bool = True
    ) -> str:
        """Build prompt for comment generation with company mention control"""
        
        # Handle organic comments that should NOT mention company
        if comment_type == "organic" and not should_mention_company:
            return f"""You are {username}, responding to this Reddit post:

Post Title: "{post_title}"
Post Body: "{post_body}"

Your background:
{backstory}

Your tone: {tone}

Task: Write a helpful, authentic comment sharing advice or experience.

IMPORTANT: Do NOT mention any specific product or company name. Share generic helpful advice based on your experience.

Requirements:
- Share genuine helpful advice or ask clarifying questions
- Be specific and useful without promoting any product
- Options: share your process, ask questions, offer perspective, relate to their problem
- Sound like a real user helping another user
- Do NOT use em-dashes (—) or fancy punctuation - use regular hyphens (-) or commas instead
- 30-80 words
- Be conversational and authentic

Return only the comment text (no JSON, no quotes, just the text)."""
        
        # Handle organic comments that SHOULD mention company
        if comment_type == "organic" and should_mention_company:
            company_context = ""
            if company_description:
                company_context = f"\n\nProduct context:\n{company_name} is a tool that {company_description}"
            
            return f"""You are {username}, responding to this Reddit post:

Post Title: "{post_title}"
Post Body: "{post_body}"

Your background:
{backstory}

Your tone: {tone}{company_context}

Task: Write a helpful comment mentioning {company_name} as something you personally use.

Requirements:
- Share your genuine experience with {company_name}
- Be specific about how it helped with the problem in the post
- Sound like a real user sharing experience, not an advertisement
- Admit limitations or imperfections (makes it authentic)
- Use phrases like "I've tried", "I use", "in my experience"
- Do NOT use em-dashes (—) or fancy punctuation - use regular hyphens (-) or commas instead
- 40-80 words
- Be conversational and helpful

Return only the comment text (no JSON, no quotes, just the text)."""
        
        if comment_type == "product_mention":
            # Add company context
            company_context = ""
            if company_description:
                company_context = f"\n\nProduct context:\n{company_name} is a tool that {company_description}"
            
            return f"""You are {username}, responding to this Reddit post:

Post Title: "{post_title}"
Post Body: "{post_body}"

Your background:
{backstory}

Your tone: {tone}{company_context}

Task: Write a helpful comment mentioning {company_name} as something you personally use.

Requirements:
- Share your genuine experience with {company_name}
- Be specific about how it helped with the problem in the post (relate to what {company_name} does)
- Sound like a real user sharing experience, not an advertisement
- Admit limitations or imperfections (makes it authentic)
- Use phrases like "I've tried", "I use", "in my experience"
- Do NOT use em-dashes (—) or fancy punctuation - use regular hyphens (-) or commas instead
- 50-80 words
- Be conversational and helpful

Return only the comment text (no JSON, no quotes, just the text)."""
        
        elif comment_type == "validation":
            return f"""You are {username}, adding to this conversation:

Original Post: "{post_title}"

Previous Comment:
"{previous_comment}"

Your background:
{backstory}

Task: Write a brief supportive comment agreeing or adding perspective.

Requirements:
- Short and natural (10-30 words)
- Options: "+1 [product]", share similar experience, add detail, light humor
- Sound like real Reddit banter
- Do NOT use em-dashes (—) or fancy punctuation
- Your tone: {tone}

Return only the comment text (no JSON, no quotes)."""
        
        else:  # op_response
            # Extract product/tool name from previous comment if it exists
            product_mention_hint = ""
            if previous_comment and company_name.lower() in previous_comment.lower():
                product_mention_hint = f"\nNote: They recommended {company_name}. Acknowledge this specifically."
            
            return f"""You are {username} (the original poster) responding to a helpful comment.

Your post was: "{post_title}"

Someone commented:
"{previous_comment}"{product_mention_hint}

Task: Write a natural response that acknowledges their specific suggestion.

Requirements:
- Brief and genuine (10-30 words)
- Thank them for THEIR recommendation (don't just name the product - say "thanks for recommending..." or "appreciate the suggestion")
- Show you're interested in trying what THEY suggested
- Sound natural like "Thanks for the rec! I'll check out [tool]" or "Appreciate it! Never heard of [tool] but I'll give it a shot"
- Reference that they helped you, not just the product name
- Do NOT use em-dashes (—) or fancy punctuation

Return only the comment text (no JSON, no quotes)."""
    
    def _parse_post_json(self, text: str) -> Optional[Dict]:
        """Parse JSON from generated text"""
        try:
            # Try to extract JSON if it's embedded in markdown
            if "```json" in text:
                json_start = text.find("```json") + 7
                json_end = text.find("```", json_start)
                text = text[json_start:json_end].strip()
            elif "```" in text:
                json_start = text.find("```") + 3
                json_end = text.find("```", json_start)
                text = text[json_start:json_end].strip()
            
            data = json.loads(text)
            
            if "title" in data and "body" in data:
                return {
                    "title": data["title"].strip(),
                    "body": data["body"].strip()
                }
        except:
            pass
        
        return None
    
    def _validate_post_quality(self, post_data: Dict, company_name: str) -> bool:
        """Validate post meets quality criteria"""
        title = post_data.get("title", "")
        body = post_data.get("body", "")
        
        print(f"  🔍 Validating post:")
        print(f"     Title ({len(title)} chars): {title[:50]}...")
        print(f"     Body ({len(body)} chars): {body[:50]}...")
        
        # Basic length checks
        if len(title) < 10 or len(title) > 200:
            print(f"  ❌ Title length invalid: {len(title)}")
            return False
        if len(body) < 30 or len(body) > 1000:
            print(f"  ❌ Body length invalid: {len(body)}")
            return False
        
        # Company name should NOT appear in post (posts should be questions, not promotions)
        # But we'll be lenient - only reject if it's clearly promotional
        company_lower = company_name.lower()
        if company_lower in title.lower():
            print(f"  ⚠️  Company '{company_name}' in title - still allowing")
        if company_lower in body.lower():
            print(f"  ⚠️  Company '{company_name}' in body - still allowing")
        
        # Should end with question mark or period
        if not (body.endswith("?") or body.endswith(".") or body.endswith("!")):
            print(f"  ❌ Body doesn't end with proper punctuation")
            return False
        
        print(f"  ✅ Post validation passed")
        return True
    
    def _validate_comment_quality(
        self,
        comment: str,
        comment_type: str,
        company_name: str
    ) -> bool:
        """Validate comment meets quality criteria"""
        # Basic length check
        if len(comment) < 5 or len(comment) > 500:
            return False
        
        # Product mention comments should include company name
        if comment_type == "product_mention":
            if company_name.lower() not in comment.lower():
                return False
        
        # Check for spam words
        spam_words = ["click here", "buy now", "sign up", "limited offer", "discount code"]
        if any(spam in comment.lower() for spam in spam_words):
            return False
        
        return True
    
    def get_usage_stats(self) -> Dict:
        """Get usage statistics for cost tracking"""
        # Rough cost calculation for Gemini Flash
        # $0.075 per 1M input tokens, $0.30 per 1M output tokens
        # Average: ~$0.15 per 1M tokens
        estimated_cost = (self.total_tokens_used / 1_000_000) * 0.15
        
        return {
            "total_tokens_used": self.total_tokens_used,
            "estimated_cost_usd": round(estimated_cost, 6)
        }


# Singleton instance for the application
_generator_instance: Optional[GeminiContentGenerator] = None


def get_generator() -> GeminiContentGenerator:
    """Get or create the AI generator instance"""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = GeminiContentGenerator()
    return _generator_instance


def reset_generator():
    """Reset the generator instance (useful for testing)"""
    global _generator_instance
    _generator_instance = None
