from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            logger.info("Health check requested")
            
            # Check if the Telegram token is available
            bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
            token_status = "available" if bot_token else "missing"
            
            # Check environment variables
            vercel_url = os.environ.get("VERCEL_URL", "not set")
            public_vercel_url = os.environ.get("NEXT_PUBLIC_VERCEL_URL", "not set")
            
            # Get Python version
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            
            # Get host information
            host = self.headers.get('Host', 'unknown')
            
            # Prepare response
            response_data = {
                "status": "ok",
                "message": "Python serverless function is working",
                "environment": {
                    "TELEGRAM_BOT_TOKEN": token_status,
                    "VERCEL_URL": vercel_url,
                    "NEXT_PUBLIC_VERCEL_URL": public_vercel_url
                },
                "python_version": python_version,
                "request_info": {
                    "host": host,
                    "path": self.path,
                    "headers": dict(self.headers)
                }
            }
            
            logger.info(f"Health check response: {response_data}")
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "error": str(e)
            }).encode('utf-8'))

