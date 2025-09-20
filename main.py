#!/usr/bin/env python3
"""
Main web service for Shopify-Pinterest Automation
Provides health check endpoint and manual trigger capabilities
"""

import os
import sys
from flask import Flask, jsonify, request
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Render"""
    return jsonify({
        'status': 'healthy',
        'service': 'shopify-pinterest-automation',
        'version': '1.0.0'
    }), 200

@app.route('/', methods=['GET'])
def home():
    """Home endpoint"""
    return jsonify({
        'message': 'Shopify-Pinterest Automation Service',
        'status': 'running',
        'endpoints': {
            'health': '/health',
            'trigger': '/trigger',
            'status': '/status'
        }
    }), 200

@app.route('/trigger', methods=['POST'])
def trigger_automation():
    """Manually trigger the automation workflow"""
    try:
        logger.info("🚀 Manual automation trigger requested")
        
        # Import and run the scheduler
        from scheduler import run_automation_workflow
        
        success = run_automation_workflow()
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Automation workflow completed successfully'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Automation workflow failed'
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Manual trigger failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Automation trigger failed: {str(e)}'
        }), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Get current system status"""
    try:
        # Check if required environment variables are set
        required_vars = [
            'SHOPIFY_API_KEY',
            'SHOPIFY_STORE_URL', 
            'SHOPIFY_COLLECTION_ID',
            'PINTEREST_ACCESS_TOKEN',
            'PINTEREST_APP_ID',
            'PINTEREST_APP_SECRET',
            'OPENAI_API_KEY',
            'SHEET_ID'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        return jsonify({
            'status': 'healthy' if not missing_vars else 'misconfigured',
            'environment_variables': {
                'configured': len(required_vars) - len(missing_vars),
                'missing': missing_vars
            },
            'service': 'shopify-pinterest-automation'
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Status check failed: {str(e)}'
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)