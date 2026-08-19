import os
from http.server import BaseHTTPRequestHandler, HTTPServer


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")


def run_health_server() -> None:
    port = int(os.getenv("PORT", "8080"))

    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()
