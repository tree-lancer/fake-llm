import json
import os
import tempfile
import threading
import urllib.request
from http.server import ThreadingHTTPServer

from src.db.store import create_api_key, history
from src.server.app import Handler


def post(url, token, payload):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode("utf-8"))


def post_text(url, token, payload):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.read().decode("utf-8")


def main():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["DB_PATH"] = f"{tmp}/capture.sqlite"
        os.environ["REPLY_STRATEGY"] = "hello"
        token = create_api_key("smoke")
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        host, port = server.server_address
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            a = post(f"http://{host}:{port}/v1/responses", token, {"model": "x", "input": "ping"})
            b = post(f"http://{host}:{port}/v1/messages", token, {"model": "y", "messages": [{"role": "user", "content": "pong"}]})
            c = post_text(f"http://{host}:{port}/v1/responses", token, {"model": "x", "input": "stream ping", "stream": True})
            rows = history(limit=10)
            assert a["output"][0]["content"][0]["text"] == "Hello"
            assert b["content"][0]["text"] == "Hello"
            assert "event: response.completed" in c
            assert len(rows) == 3
            assert rows[0]["api_key_name"] == "smoke"
            print("ok")
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    main()
