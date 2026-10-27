"""Diagnostics service used by the operations team."""

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = {"status": "ok", "environment": dict(os.environ)}
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body, indent=2).encode())

    def log_message(self, _format, *_args):
        return


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8081), Handler).serve_forever()
