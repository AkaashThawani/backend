# OGTool Backend

FastAPI backend for the Organic Growth Tool - automated Reddit content generation and scheduling with advanced AI-driven algorithms.

## Features

- **Advanced Content Generation**: AI-powered content calendar generation with 7-day coverage
- **Strict Deduplication**: Intelligent deduplication for posts and comments to ensure quality
- **AI-Only Generation**: Pure AI-generated content with no template fallbacks
- **Context-Aware Comments**: Company-mentioning comments that understand parent post context
- **Campaign Management**: Full campaign lifecycle management
- **Post & Comment Scheduling**: Automated scheduling across Reddit communities
- **Persona Management**: Multi-persona support for diverse perspectives
- **Promotion Strategy**: Configurable promotion strategies
- **Health Monitoring**: Comprehensive health checks and metrics

## Algorithm Highlights

### Content Generation Algorithm
- **7-Day Coverage**: Generates content across all 7 days of the week (Monday-Sunday)
- **Smart Deduplication**: Attempts unique content first, fills gaps when needed for complete coverage
- **AI-Only Content**: All posts and comments are 100% AI-generated with no template fallbacks
- **Context Awareness**: Company comments have full access to parent post content for relevance
- **Natural Conversations**: Creates realistic Reddit discussion threads

### Key Capabilities
- **Post Generation**: Creates diverse, engaging posts across multiple subreddits
- **Comment Threads**: Generates contextual comment chains with company mentions
- **Deduplication Logic**: Prevents repetitive content while ensuring coverage
- **Persona Rotation**: Uses different personas for varied perspectives
- **Keyword Targeting**: Natural integration of target keywords

## Tech Stack

- **Framework**: FastAPI
- **Database**: SQLite (SQLAlchemy ORM)
- **AI**: Google Gemini AI (primary), OpenAI GPT-4 (fallback)
- **Python**: 3.8+
- **Validation**: Pydantic 2.9.2

## Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file:

```env
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=sqlite:///./ogtool.db
```

### 4. Initialize Database

```bash
python init_db.py
```

### 5. Seed Sample Data (Optional)

```bash
python seed_data.py
```

### 6. Run Server

```bash
python -m uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Key Endpoints

- `GET /api/health` - Health check
- `GET /api/metrics` - Dashboard metrics
- `GET /api/campaigns` - List campaigns
- `POST /api/campaigns` - Create campaign
- `POST /api/campaigns/{id}/generate` - Generate content

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app
│   ├── routes.py        # API endpoints
│   ├── models.py        # Database models
│   ├── schemas.py       # Pydantic schemas
│   ├── algorithm.py     # Content generation
│   └── ai_service.py    # OpenAI integration
├── requirements.txt
├── init_db.py
└── seed_data.py
```

## Git Setup

To initialize this as a separate Git repository:

```bash
cd backend
git init
git add .
git commit -m "Initial commit: OGTool backend"
git branch -M main
git remote add origin <your-backend-repo-url>
git push -u origin main
```

## Algorithm Details

### Content Generation Process

1. **Post Distribution**: For 7+ posts per week, distributes content across all 7 days
2. **Deduplication Strategy**:
   - Attempts to generate unique posts first
   - If deduplication prevents 7-day coverage, fills gaps with additional content
   - Ensures complete week coverage while minimizing duplicates
3. **Comment Generation**:
   - Creates contextual comment threads
   - Company mentions are naturally integrated based on post content
   - Strict deduplication prevents repetitive comments
4. **AI Integration**:
   - Primary: Google Gemini AI for content generation
   - Fallback: OpenAI GPT-4 for reliability
   - All content is 100% AI-generated with no template fallbacks

### Recent Improvements

- ✅ **7-Day Coverage**: Algorithm now generates content for all 7 days of the week
- ✅ **Strict Deduplication**: Advanced deduplication for both posts and comments
- ✅ **AI-Only Generation**: Removed all template fallbacks for pure AI content
- ✅ **Context Awareness**: Company comments understand parent post content
- ✅ **Deployment Compatibility**: Updated dependencies for better deployment support

## Deployment

### Render Deployment

1. **Connect Repository**: Connect your GitHub repository to Render
2. **Service Configuration**:
   - **Service Type**: Web Service
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`

3. **Environment Variables**:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   DATABASE_URL=sqlite:///./ogtool.db
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

4. **Python Version**: The app is configured for Python 3.11.0

### Local Development

See `SETUP.md` for detailed local setup instructions.

**Note**: The application uses Pydantic 2.8.2 with pre-compiled wheels for better deployment compatibility on platforms like Render. The `render.yaml` file provides optimized deployment configuration.
