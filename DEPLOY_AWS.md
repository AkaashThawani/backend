# AWS Elastic Beanstalk Deployment Guide

## Prerequisites
- AWS Account with Elastic Beanstalk access
- Your code committed to Git repository

## Step 1: Create Elastic Beanstalk Application

1. Go to [AWS Elastic Beanstalk Console](https://console.aws.amazon.com/elasticbeanstalk)
2. Click **"Create Application"**
3. Configure:
   - **Application name**: `ogtool-backend`
   - **Platform**: `Python`
   - **Platform branch**: `Python 3.11 running on 64bit Amazon Linux 2`
   - **Application code**: Upload source code (ZIP)

## Step 2: Upload Your Code

1. Create a ZIP file of your project (exclude venv/, .git/, etc.)
2. In EB console, go to your application
3. Click **"Upload and deploy"**
4. Upload your ZIP file
5. Click **"Deploy"**

## Step 3: Configure Environment Variables

In EB Console → Your Environment → Configuration → Software:
```
OPENAI_API_KEY = your_openai_key
GEMINI_API_KEY = your_gemini_key
DATABASE_URL = sqlite:///./ogtool.db
```

## Step 4: Access Your App

Once deployed, your app will be available at:
`http://your-app-name.region.elasticbeanstalk.com`

## Troubleshooting

- **Python version issues**: Check `.platform/python/runtime.txt`
- **Database errors**: Check EB logs for initialization issues
- **Port issues**: Ensure Procfile uses `$PORT` environment variable

## Free Tier Limits
- 750 hours/month of t2.micro instances
- No additional charges for first year
