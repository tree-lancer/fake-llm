import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from src.dashboard.view import render
from src.db.store import capture, find_api_key
from src.server.anthropic import messages as anthropic_messages
from src.server.openai import chat as openai_chat
from src.server.openai import responses as openai_responses
from src.server.sse import encode
from src.server.strategy import load_strategy


def bearer(headers):
    value = headers.get("authorization") or headers.get("Authorization") or ""
    if value.lower().startswith("bearer "):
        return value[7:].strip()
    return value.strip()


class Handler(BaseHTTPRequestHandler):
    server_version = "wwsai/0.1"

    def log_message(self, fmt, *args):
        return

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/dashboard"):
            self.send_html(render())
            return
        if path == "/health":
            self.send_json({"ok": True})
            return
        self.send_json({"error": "not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        raw = self.rfile.read(int(self.headers.get("content-length", "0") or "0")).decode("utf-8", "replace")
        payload = parse_json(raw)
        api_key = find_api_key(bearer(self.headers))
        if not api_key:
            self.send_json({"error": {"message": "invalid api key", "type": "auth_error"}}, 401)
            return
        strategy = load_strategy()
        headers = {k: v for k, v in self.headers.items()}
        if path == "/v1/responses":
            message = openai_responses.extract_message(payload)
            text = strategy.reply(api_key, message, {"provider": "openai", "endpoint": "responses", "payload": payload})
            response = openai_responses.response(payload, text)
            created_at = capture(api_key, "openai", "responses", "POST", path, headers, raw, response, strategy.name)
            capture_log(api_key, created_at, message)
            if payload.get("stream") is True:
                self.send_sse(openai_responses.stream_events(payload, text))
                return
            self.send_json(response)
            return
        if path == "/v1/chat/completions":
            message = openai_chat.extract_message(payload)
            text = strategy.reply(api_key, message, {"provider": "openai", "endpoint": "chat.completions", "payload": payload})
            response = openai_chat.response(payload, text)
            created_at = capture(api_key, "openai", "chat.completions", "POST", path, headers, raw, response, strategy.name)
            capture_log(api_key, created_at, message)
            if payload.get("stream") is True:
                self.send_sse(openai_chat.stream_events(payload, text), done=True)
                return
            self.send_json(response)
            return
        if path == "/v1/messages":
            message = anthropic_messages.extract_message(payload)
            text = strategy.reply(api_key, message, {"provider": "anthropic", "endpoint": "messages", "payload": payload})
            response = anthropic_messages.response(payload, text)
            created_at = capture(api_key, "anthropic", "messages", "POST", path, headers, raw, response, strategy.name)
            capture_log(api_key, created_at, message)
            self.send_json(response)
            return
        self.send_json({"error": "not found"}, 404)

    def send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, text, status=200):
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "text/html; charset=utf-8")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_sse(self, events, status=200, done=False):
        self.send_response(status)
        self.send_header("content-type", "text/event-stream; charset=utf-8")
        self.send_header("cache-control", "no-cache")
        self.send_header("connection", "close")
        self.end_headers()
        for event, data in events:
            self.wfile.write(encode(event, data))
            self.wfile.flush()
        if done:
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()


def parse_json(raw):
    try:
        return json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}


def capture_log(api_key, created_at, message):
    value = re.sub(r"\s+", " ", message or "").strip()
    if len(value) > 500:
        value = value[:497] + "..."
    print(f'[{api_key["name"]}][{created_at}]<{value}>', flush=True)


def main():
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8787"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Base Url: http://{host}:{port}/v1", flush=True)
    print("Create API key: ./run.sh api-key gen <name>", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
