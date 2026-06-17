import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.database import init_db
from app.routes.operations import create_operation, list_operations
from app.routes.simulation import run_simulation

init_db()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_json({"message": "Backend API is running"})
        elif parsed.path == "/operations":
            self._send_json(list_operations())
        else:
            self._send_json({"detail": "Not found"}, status=404)

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        payload = self.rfile.read(length)
        data = json.loads(payload.decode("utf-8")) if payload else {}

        if parsed.path == "/operations":
            result = create_operation(data)
            self._send_json(result, status=201)
        elif parsed.path == "/simulation":
            result = run_simulation(data)
            self._send_json(result)
        else:
            self._send_json({"detail": "Not found"}, status=404)

    def _send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8000), Handler)
    print("Server running at http://127.0.0.1:8000")
    server.serve_forever()
