# OGTool Backend

FastAPI backend for the Organic Growth Tool - automated Reddit content generation and scheduling.

## Features

- Content calendar generation with AI
- Campaign management
- Post and comment scheduling
- Persona management
- Promotion strategy configuration
- Health monitoring endpoint

## Tech Stack

- **Framework**: FastAPI
- **Database**: SQLite (SQLAlchemy ORM)
- **AI**: OpenAI GPT-4
- **Python**: 3.8+

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

## Deployment

See `SETUP.md` for deployment instructions.
