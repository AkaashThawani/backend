# Backend Setup Guide

## Virtual Environment Setup (Recommended)

To avoid conflicts with global packages (chromadb, langchain, etc.), use a virtual environment:

### Windows:
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Mac/Linux:
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Backend

### 1. Ensure .env file exists
```bash
# Check if .env exists
ls .env

# If not, copy from example
cp .env.example .env

# Add your Gemini API key
# Edit .env and add: GEMINI_API_KEY=your_key_here
```

### 2. Start the FastAPI server
```bash
# Make sure virtual environment is activated
# (venv should appear in your terminal prompt)

# Run the server
python -m uvicorn app.main:app --reload --port 8000
```

Server will be available at: http://localhost:8000

### 3. Test the API
Open in browser:
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Deactivating Virtual Environment

When you're done:
```bash
deactivate
```

## Troubleshooting

### Dependency Conflicts
If you see dependency conflict errors, you likely installed packages globally. The virtual environment isolates our project dependencies from global packages.

**Solution:** Always activate the virtual environment before running any Python commands for this project.

### API Key Issues
If you get "GEMINI_API_KEY not found" errors:
1. Check that `.env` file exists in `backend/` directory
2. Verify the key is correctly formatted: `GEMINI_API_KEY=your_actual_key`
3. Restart the server after updating `.env`

### Import Errors
If you get import errors for `google.generativeai`:
```bash
# Activate venv first
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Mac/Linux

# Then install
pip install -r requirements.txt
```

## Project Structure

```
backend/
├── venv/              # Virtual environment (don't commit)
├── .env               # Environment variables (don't commit)
├── .env.example       # Template for .env
├── requirements.txt   # Python dependencies
├── app/
│   ├── __init__.py
│   ├── main.py        # FastAPI app
│   ├── routes.py      # API endpoints
│   ├── models.py      # Database models
│   ├── schemas.py     # Pydantic schemas
│   ├── algorithm.py   # Content generation algorithm
│   └── ai_service.py  # Gemini AI integration
└── docs/
    └── content-generation-algorithm.md
```

## Next Steps

1. ✅ Create virtual environment
2. ✅ Activate virtual environment  
3. ✅ Install dependencies
4. ✅ Set up .env file
5. ✅ Start the server
6. 🧪 Test content generation via API
