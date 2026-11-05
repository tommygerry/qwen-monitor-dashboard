#!/usr/bin/env python3
"""Qwen Monitor — jederzeit den Monitor des Qwen-Modells auf dem Handy ablesen.

Steht als kleiner Proxy zwischen Browser und dem Strata-Server auf dem Handy
(Standard: http://100.xx.yy.zz:8080). Der Strata-Server sendet keine CORS-
Header, deshalb laufen Dashboard und Datenabruf über diesen gleichen Host.

Start:   python3 monitor.py
 config: STRATA_URL=... PORT=... python3 monitor.py
Dashboard: http://localhost:8765  (auch erreichbar über Tailscale an der Mac-IP)
"""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import URLError
from urllib.request import urlopen

STRATA = os.environ.get("STRATA_URL", "http://100.xx.yy.zz:8080")
MACMON = os.environ.get("MACMON_URL", "http://100.xx.yy.zz:9090/json")
PORT = int(os.environ.get("PORT", "8765"))
HERE = os.path.dirname(os.path.abspath(__file__))


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            path = os.path.join(HERE, "dashboard.html")
            with open(path, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)
        elif self.path.startswith("/health") or self.path.startswith("/metrics"):
            self._forward(STRATA + self.path, "Strata")
        elif self.path.startswith("/temps"):
            self._forward(MACMON, "macmon (macmon serve auf dem Mac Studio)")
        else:
            self.send_error(404)

    def _forward(self, url, label):
        try:
            with urlopen(url, timeout=10) as r:
                data = r.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)
        except Exception as exc:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"{label} nicht erreichbar: {exc}"}).encode())

    def log_message(self, format, *args):
        pass  # ruhig


if __name__ == "__main__":
    print(f"Qwen Monitor: http://localhost:{PORT}  (Quelle: {STRATA})", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
