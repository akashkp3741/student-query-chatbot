"""Local CampusGuide web app.

The module intentionally uses Python's standard library so the project can be run in a classroom, lab, or restricted environment without a package install. It exposes GET /api/info and POST /api/chat.
"""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from model import Chatbot

ROOT = Path(__file__).resolve().parent
bot = Chatbot()
ASSETS = {'/': ('index.html', 'text/html; charset=utf-8'),
          '/style.css': ('style.css', 'text/css; charset=utf-8'),
          '/chat.js': ('chat.js', 'text/javascript; charset=utf-8'),
          '/logo.svg': ('logo.svg', 'image/svg+xml; charset=utf-8')}


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, content, mime='application/json; charset=utf-8'):
        raw = json.dumps(content).encode('utf-8') if isinstance(content, dict) else content
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        """Serve the public metadata endpoint or a static asset."""
        path = urlsplit(self.path).path
        if path == '/api/info':
            return self.reply(200, {'college': bot.data['college'], 'sample_data': bot.data['sample_data'],
                                    'suggestions': bot.data['suggestions'], 'intents': len(bot.intents),
                                    'questions': len(bot.samples)})
        if path in ASSETS:
            name, mime = ASSETS[path]
            return self.reply(200, (ROOT / 'static' / name).read_bytes(), mime)
        self.reply(404, {'error': 'Not found'})

    def do_POST(self):
        """Validate a chat payload and return the classifier response."""
        if self.path != '/api/chat':
            return self.reply(404, {'error': 'Not found'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if size < 1 or size > 8192:
                if 8192 < size <= 65536:
                    self.rfile.read(size)  # Drain small rejected bodies so Windows delivers the error response.
                return self.reply(413, {'error': 'Request must contain 1 to 8192 bytes.'})
            payload = json.loads(self.rfile.read(size))
            message = payload.get('message') if isinstance(payload, dict) else None
            if not isinstance(message, str) or not message.strip() or len(message) > 500:
                return self.reply(400, {'error': 'Enter a question between 1 and 500 characters.'})
        except (ValueError, UnicodeDecodeError):
            return self.reply(400, {'error': 'Invalid JSON request.'})
        self.reply(200, bot.predict(message.strip()))

    def log_message(self, fmt, *args):
        # Do not log students' question text.
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the CampusGuide mini project locally.')
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'CampusGuide is running at http://127.0.0.1:{args.port}', flush=True)
    print('Press Ctrl+C to stop.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
