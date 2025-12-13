# Elastic Beanstalk expects a file named 'application.py' with a variable named 'application'
# This file serves as a wrapper to import your FastAPI app

from app.main import app as application

# For local development/testing, you can also expose 'app'
app = application
