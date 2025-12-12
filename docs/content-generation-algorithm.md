# Content Generation Algorithm Documentation

## Overview

The Reddit Mastermind content generation algorithm creates authentic, engaging Reddit conversations that drive organic visibility and inbound leads for clients. The algorithm generates posts and comments that look natural, not manufactured.

## Goal

Generate Reddit content calendars that:
- Drive upvotes, views, and inbound leads
- Look like real conversations (9/10 quality, not 3/10)
- Eventually rank on Google
- Get cited by LLMs (ChatGPT, Claude, etc.)

---

## Input Structure

### Required Inputs

```python
{
  "company_info": {
    "name": "SlideForge",
    "description": "AI-powered presentation tool that helps create professional slides",
    "website": "slideforge.ai"
  },
  "personas": [
    {
      "username": "riley_ops",
      "backstory": "Head of operations at a SaaS startup...",
      "tone_style": "Professional"
    },
    {
      "username": "jordan_consults",
      "backstory": "Independent consultant who works with early stage founders...",
      "tone_style": "Professional"
    },
    # Minimum 2 personas required
  ],
  "subreddits": [
    "r/PowerPoint",
    "r/ClaudeAI",
    "r/Canva"
  ],
  "keywords": [
    {
      "id": "K1",
      "keyword": "AI presentation maker"
    },
    {
      "id": "K8",
      "keyword": "Claude vs Slideforge"
    }
  ],
  "posts_per_week": 3,
  "week_start": "2025-12-08" # Optional, defaults to next Monday
}
```

---

## Output Structure

### Posts Table

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| post_id | string | Unique identifier | "P1" |
| subreddit | string | Target subreddit | "r/PowerPoint" |
| title | string | Post title | "Best AI Presentation Maker?" |
| body | string | Post body | "Just like it says in the title..." |
| author_username | string | Posting persona | "riley_ops" |
| timestamp | datetime | Scheduled time | "2025-12-08 14:12" |
| keyword_ids | array | Targeted keywords | ["K1", "K14", "K4"] |

### Comments Table

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| comment_id | string | Unique identifier | "C1" |
| post_id | string | Parent post | "P1" |
| parent_comment_id | string | Parent comment (null if top-level) | null or "C1" |
| comment_text | string | Comment content | "I've tried a bunch of tools..." |
| username | string | Commenting persona | "jordan_consults" |
| timestamp | datetime | Scheduled time | "2025-12-08 14:33" |

---

## Content Generation Strategy

### Post Generation

**Purpose:** Create the initial question/discussion that invites engagement

**Approach:**
1. Select persona (rotate for variety)
2. Select subreddit (distribute evenly)
3. Select 1-3 keywords to target
4. Generate authentic question/discussion

**Quality Criteria:**
- ✅ Sounds like a real person with a real problem
- ✅ Specific enough to be helpful
- ✅ Open-ended to invite discussion
- ✅ Appropriate for subreddit culture
- ✅ Natural language (not robotic or templated)
- ✅ Does NOT mention the product in the post

**Example (Good):**
```
Title: "Best AI Presentation Maker?"
Body: "Just like it says in the title, what is the best AI 
Presentation Maker? I'm looking for something that makes high 
quality slides I can edit afterwards. Any help appreciated."
```

**Example (Bad - Too Generic):**
```
Title: "AI tools?"
Body: "Recommendations?"
```

### Comment Generation

**Purpose:** Create natural conversation that introduces the product organically

**Comment Flow:**

**Comment 1 (Product Mention):**
- Different persona than post author
- Shares personal experience with product
- Mentions specific benefits
- Honest (admits imperfections)
- 50-80 words
- Timing: 10-30 minutes after post

**Example:**
```
"I've tried a bunch of tools. Slideforge is the only one that 
doesn't make me fight the layout. Still fix things after, but 
it's a decent starting point."
```

**Comment 2 (Validation):**
- Another different persona
- Brief agreement or additional perspective
- 10-30 words
- Timing: 15-30 minutes after first comment

**Example:**
```
"+1 Slideforge"
```

**Comment 3 (OP Response):**
- Original poster responds
- Shows interest/gratitude
- Natural follow-up
- 10-20 words
- Timing: 10-30 minutes after validation

**Example:**
```
"Sweet I'll check it out!!"
```

**Quality Criteria for Comments:**
- ✅ Personal experience tone ("I've tried", "I use")
- ✅ Specific details (not generic praise)
- ✅ Not salesy or promotional
- ✅ Varied responses (not repetitive)
- ✅ Natural timing between comments
- ✅ Honest (mentions limitations)

---

## Sample Output

### Week of Dec 8-14, 2025 (3 posts)

**Post P1:**
```
Subreddit: r/PowerPoint
Title: "Best AI Presentation Maker?"
Body: "Just like it says in the title, what is the best AI Presentation 
Maker? I'm looking for something that makes high quality slides I can edit 
afterwards. Any help appreciated."
Author: riley_ops
Time: Dec 8, 2:12 PM
Keywords: K1, K14, K4

Comments:
  C1 [jordan_consults, 2:33 PM]: "I've tried a bunch of tools. Slideforge 
  is the only one that doesn't make me fight the layout. Still fix things 
  after, but it's a decent starting point."
  
  C2 [emily_econ, 2:49 PM, reply to C1]: "+1 Slideforge"
  
  C3 [riley_ops, 3:02 PM, reply to C2]: "Sweet I'll check it out!!"
```

**Post P2:**
```
Subreddit: r/ClaudeAI
Title: "Slideforge VS Claude for slides?"
Body: "Trying to figure out what's the best one for making presentations."
Author: riley_ops
Time: Dec 10, 9:03 AM
Keywords: K8, K1, K14

Comments:
  C4 [jordan_consults, 9:25 AM]: "I use Claude for brainstorming, but for 
  slides it sorta guesses a layout and hopes for the best. Slideforge feels 
  more structured."
  
  C5 [alex_sells, 9:41 AM, reply to C4]: "Yea Claude's slide output always 
  looks really funky lol"
  
  C6 [priya_pm, 10:02 AM, reply to C4]: "Same here. Claude is fine for 
  internal notes but for anything customer facing we end up using Slideforge."
```

**Post P3:**
```
Subreddit: r/Canva
Title: "Slideforge vs Canva for slides?"
Body: "I love Canva but I'm trying to automate more of my slides, especially 
with image gen + layouts. Heard about Slideforge but unsure if it's any good."
Author: riley_ops
Time: Dec 11, 6:44 PM
Keywords: K7, K10, K14

Comments:
  C7 [jordan_consults, 7:01 PM]: "Canva is good if I already know the vibe 
  I want. Otherwise I end up scrolling templates forever. Slideforge gives me 
  a rough structure first, then I make it pretty in Canva."
  
  C8 [emily_econ, 7:14 PM, reply to C7]: "+1 Slideforge. I put it into canva 
  afterwards too"
  
  C9 [alex_sells, 7:37 PM]: "I hate picking fonts lol. Slideforge's defaults 
  save my sanity."
```

---

## Algorithm Flow

### 1. Initialize
- Load campaign data (company, personas, subreddits, keywords)
- Set week start date
- Initialize tracking (subreddit usage, persona usage)

### 2. Generate Posts
```python
for i in range(posts_per_week):
    # Select context
    persona = select_least_used_persona()
    subreddit = select_least_used_subreddit()
    keywords = select_keywords(1-3)
    day_offset = distribute_across_week(i)
    
    # Generate post (AI or template)
    post = generate_post(persona, subreddit, keywords)
    
    # Schedule realistically (8am-8pm)
    post.timestamp = week_start + day_offset + random_hour(8-20)
    
    # Save post
    posts.append(post)
```

### 3. Generate Comments
```python
for post in posts:
    # Get available commenters (not post author)
    commenters = get_other_personas(post.author)
    
    # Comment 1: Product mention (10-30 min after post)
    c1 = generate_product_mention_comment(
        post, 
        commenters[0],
        company_name
    )
    c1.timestamp = post.timestamp + minutes(10-30)
    
    # Comment 2: Validation (15-30 min after c1)
    c2 = generate_validation_comment(
        post,
        c1,
        commenters[1]
    )
    c2.timestamp = c1.timestamp + minutes(15-30)
    c2.parent_comment_id = c1.comment_id
    
    # Comment 3: OP response (10-30 min after c2)
    c3 = generate_op_response(
        post,
        c1,
        post.author
    )
    c3.timestamp = c2.timestamp + minutes(10-30)
    c3.parent_comment_id = c2.comment_id
    
    comments.extend([c1, c2, c3])
```

### 4. Return Calendar
```python
return ContentCalendar(
    posts=posts,
    comments=comments,
    week_start=week_start,
    week_end=week_start + days(6)
)
```

---

## AI Integration Plan

### Phase 1: Replace Templates with AI

**Current:** Uses hardcoded templates
```python
POST_TEMPLATES = [
    {"title": "Best {keyword} tools in 2024?", ...}
]
```

**Future:** Use Gemini AI
```python
def generate_post(persona, subreddit, keyword):
    prompt = build_post_prompt(persona, subreddit, keyword)
    response = gemini.generate(prompt)
    return parse_post(response)
```

### Phase 2: Prompt Engineering

**Post Generation Prompt:**
```
You are {persona.username}.
Background: {persona.backstory}

Task: Write a Reddit post for {subreddit} asking about "{keyword}".

Requirements:
- Write in first person as this character
- Include specific details from your background
- Sound natural, not promotional
- Create a post that invites discussion
- Do NOT mention {company.name} in the post
- Be curious and genuine

Return JSON:
{
  "title": "...",
  "body": "..."
}
```

**Comment Generation Prompt:**
```
Post context:
Title: "{post.title}"
Body: "{post.body}"
Author: {post.author}

You are {commenter.username} responding.
Background: {commenter.backstory}

Task: Write a helpful comment mentioning {company.name}.

Requirements:
- Share your personal experience with {company.name}
- Be specific about how it helped with {keyword}
- Sound like a real user, not an ad
- Admit limitations or imperfections
- 50-80 words

Return: Just the comment text (no JSON)
```

### Phase 3: Quality Validation

**Automated Checks:**
- Length validation (not too short/long)
- No spam words ("click here", "buy now", etc.)
- Persona consistency (uses backstory details)
- Variety (not repeating phrases)

**Manual Review (Optional):**
- Preview generated calendar
- Regenerate individual posts/comments
- Approve before scheduling

---

## Cost Optimization (Gemini Flash)

**Expected Costs:**
- Post generation: ~500 tokens = $0.0000375 per post
- Comment generation: ~300 tokens = $0.0000225 per comment
- Full campaign (3 posts + 9 comments): ~$0.0005 total

**Strategies:**
- Use Gemini Flash (cheapest model)
- Set max token limits (200-300 per generation)
- Cache common prompts
- Batch generate when possible

---

## Edge Cases to Handle

1. **Overposting in a subreddit**
   - Track subreddit usage
   - Distribute posts evenly
   - Max 1-2 posts per subreddit per week

2. **Overlapping topics**
   - Track keyword usage
   - Vary post types and angles
   - Ensure each post feels unique

3. **Awkward persona interactions**
   - Never have same persona post and comment
   - Rotate commenting personas
   - Natural timing between responses

4. **Spam detection**
   - Vary language and structure
   - Realistic timing (not instant responses)
   - Different personas for different roles

5. **Low quality output**
   - Validate generated content
   - Retry if below quality threshold
   - Fallback to better templates if AI fails

---

## Success Metrics

**Quality Indicators:**
- Would a human believe this is real? (9/10 target)
- Does it invite genuine engagement?
- Is the product mention natural?
- Are conversations varied and authentic?

**Engagement Metrics:**
- Upvotes from real Reddit users
- Comments from real Reddit users
- Click-through to company website
- Inbound leads generated

**SEO Metrics:**
- Google ranking for target keywords
- Citations in LLM responses
- Backlinks and mentions

---

## Next Steps

1. ✅ Document algorithm design
2. ⏳ Implement AI service (Gemini integration)
3. ⏳ Update ContentCalendarGenerator to use AI
4. ⏳ Add quality validation checks
5. ⏳ Test with varied inputs
6. ⏳ Deploy and monitor performance
