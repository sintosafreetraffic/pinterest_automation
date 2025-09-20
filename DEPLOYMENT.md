# Shopify-Pinterest Automation - Render Deployment Guide

## Overview
This guide will help you deploy the Shopify-Pinterest automation system to Render with scheduled execution twice daily.

## Prerequisites
- Render account
- All environment variables configured
- GitHub repository with the code

## Deployment Steps

### 1. Prepare Your Repository
Ensure your repository contains:
- `render.yaml` - Render configuration
- `requirements.txt` - Python dependencies
- `main.py` - Web service
- `scheduler.py` - Automation scheduler
- All your automation code files

### 2. Deploy to Render

#### Option A: Using Render Dashboard
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Blueprint"
3. Connect your GitHub repository
4. Render will automatically detect the `render.yaml` file
5. Review the configuration and deploy

#### Option B: Using Render CLI
```bash
# Install Render CLI
npm install -g @render/cli

# Login to Render
render login

# Deploy from your repository
render deploy
```

### 3. Configure Environment Variables
In the Render dashboard, set these environment variables:

**Required Variables:**
```
SHOPIFY_API_KEY=your_shopify_api_key
SHOPIFY_STORE_URL=https://your-store.myshopify.com
SHOPIFY_COLLECTION_ID=your_collection_id
PINTEREST_ACCESS_TOKEN=your_pinterest_token
PINTEREST_APP_ID=your_pinterest_app_id
PINTEREST_APP_SECRET=your_pinterest_app_secret
OPENAI_API_KEY=your_openai_key
OPEN_API_TOKEN=your_openai_token
DEEPSEEK_API_KEY=your_deepseek_key
SHEET_ID=your_google_sheet_id
```

### 4. Verify Deployment
1. Check the web service health: `https://your-app.onrender.com/health`
2. Check system status: `https://your-app.onrender.com/status`
3. Manually trigger automation: `POST https://your-app.onrender.com/trigger`

## Scheduled Execution

The system is configured to run twice daily:
- **9:00 AM UTC** (morning execution)
- **9:00 PM UTC** (evening execution)

### Manual Execution
You can manually trigger the automation by sending a POST request to `/trigger` endpoint.

## Monitoring

### Logs
- View logs in Render dashboard
- Check `automation.log` file for detailed execution logs

### Health Checks
- Web service: `/health`
- System status: `/status`
- Manual trigger: `/trigger`

## Troubleshooting

### Common Issues

1. **Environment Variables Missing**
   - Check all required variables are set in Render dashboard
   - Verify variable names match exactly

2. **API Rate Limits**
   - The system includes rate limiting for Shopify API calls
   - Pinterest API calls are also rate-limited

3. **Google Sheets Access**
   - Ensure service account has access to the Google Sheet
   - Verify sheet ID is correct

4. **Scheduler Not Running**
   - Check cron job configuration in Render
   - Verify scheduler service is running

### Debug Mode
To enable debug logging, set environment variable:
```
DEBUG=true
```

## Architecture

The deployment includes:
- **Web Service**: Health checks and manual triggers
- **Cron Job**: Scheduled automation execution
- **Rate Limiting**: Respects API rate limits
- **Error Handling**: Comprehensive error logging
- **Multi-pass Verification**: Ensures complete processing

## Security

- All API keys are stored as environment variables
- No sensitive data in code repository
- Rate limiting prevents API abuse
- Comprehensive error logging for monitoring

## Support

For issues or questions:
1. Check the logs in Render dashboard
2. Verify environment variables
3. Test individual components manually
4. Check API rate limits and quotas
