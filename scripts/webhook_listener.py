#!/usr/bin/env python3
import hashlib
import hmac
import json
import logging
import os
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuration
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "ecms-webhook-secret-change-me")
DEPLOY_SCRIPT = "/home/ubuntu/ecms/scripts/deploy.sh"
LOG_FILE = "/home/ubuntu/ecms/logs/webhook.log"
PORT = 9100

# Setup logging
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify GitHub webhook signature."""
    if not signature.startswith('sha256='):
        return False
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f'sha256={expected}', signature)


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != '/webhook':
            self.send_response(404)
            self.end_headers()
            return

        # Read body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        # Verify signature
        signature = self.headers.get('X-Hub-Signature-256', '')
        if not verify_signature(body, signature):
            logger.warning("Invalid webhook signature")
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b'Invalid signature')
            return

        # Parse payload
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Invalid JSON')
            return

        # Check event type
        event = self.headers.get('X-GitHub-Event', '')
        if event != 'push':
            logger.info(f"Ignoring event: {event}")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Event ignored')
            return

        # Check branch
        ref = payload.get('ref', '')
        if ref != 'refs/heads/main':
            logger.info(f"Ignoring push to: {ref}")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Branch ignored')
            return

        # Trigger deployment
        pusher = payload.get('pusher', {}).get('name', 'unknown')
        commits = len(payload.get('commits', []))
        logger.info(f"Push from {pusher} with {commits} commits. Triggering deploy...")

        try:
            result = subprocess.run(
                [DEPLOY_SCRIPT],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                logger.info("Deployment triggered successfully")
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'Deploy triggered')
            else:
                logger.error(f"Deploy script failed: {result.stderr}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b'Deploy failed')
        except subprocess.TimeoutExpired:
            logger.error("Deploy script timed out")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'Deploy timeout')
        except Exception as e:
            logger.error(f"Error running deploy: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'Deploy error')

    def do_GET(self):
        """Health check endpoint."""
        if self.path == '/health':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress default HTTP logging."""
        pass


def main():
    server = HTTPServer(('0.0.0.0', PORT), WebhookHandler)
    logger.info(f"Webhook listener started on port {PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down webhook listener")
        server.shutdown()


if __name__ == '__main__':
    main()
