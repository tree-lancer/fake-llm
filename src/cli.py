import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

from src.db import store


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".runtime"
PID_FILE = RUNTIME / "server.pid"
URL_FILE = RUNTIME / "server.url"
LOG_FILE = RUNTIME / "server.log"


def base_url(url):
    return f"{url.rstrip('/')}/v1"


def print_start(url):
    print(f"Base Url: {base_url(url)}")
    print("Create API key: ./run.sh api-key gen <name>")


def load_env():
    config = ROOT / "src" / "config" / "config.example"
    if config.exists():
        for line in config.read_text().splitlines():
            if not line or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key, value)


def python_cmd():
    return [sys.executable]


def up(args):
    load_env()
    RUNTIME.mkdir(exist_ok=True)
    if status_running():
        print_start(URL_FILE.read_text().strip())
        return 0
    env = os.environ.copy()
    host = env.get("HOST", "127.0.0.1")
    port = free_port(host, int(env.get("PORT", "8787")))
    env["PORT"] = str(port)
    log = LOG_FILE.open("ab")
    proc = subprocess.Popen(python_cmd() + ["-m", "src.server.app"], cwd=ROOT, env=env, stdout=log, stderr=log, start_new_session=True)
    PID_FILE.write_text(str(proc.pid))
    url = f"http://{host}:{port}"
    URL_FILE.write_text(url)
    time.sleep(0.2)
    if proc.poll() is not None:
        print("failed")
        show_log_tail()
        return 1
    print_start(url)
    return 0


def serve(args):
    load_env()
    RUNTIME.mkdir(exist_ok=True)
    env = os.environ
    host = env.get("HOST", "127.0.0.1")
    port = free_port(host, int(env.get("PORT", "8787")))
    env["PORT"] = str(port)
    URL_FILE.write_text(f"http://{host}:{port}")
    from src.server.app import main as server_main
    server_main()
    return 0


def down(args):
    if not PID_FILE.exists():
        print("stopped")
        return 0
    pid = int(PID_FILE.read_text().strip())
    try:
        os.kill(pid, 15)
    except ProcessLookupError:
        pass
    PID_FILE.unlink(missing_ok=True)
    print("stopped")
    return 0


def status(args):
    if status_running():
        print(f"running {base_url(URL_FILE.read_text().strip())}")
    else:
        print("stopped")
    return 0


def status_running():
    if not PID_FILE.exists():
        return False
    try:
        os.kill(int(PID_FILE.read_text().strip()), 0)
        return True
    except Exception:
        PID_FILE.unlink(missing_ok=True)
        return False


def free_port(host, start):
    for port in range(start, start + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
                return port
            except OSError:
                continue
    raise RuntimeError("no free port")


def show_log_tail():
    if not LOG_FILE.exists():
        return
    lines = LOG_FILE.read_text(errors="replace").splitlines()[-12:]
    for line in lines:
        print(line)


def api_key(args):
    if args.action == "gen":
        token = store.create_api_key(args.name)
        print(token)
        return 0
    if args.action == "list":
        for item in store.list_api_keys():
            print(f'{item["name"]} {item["prefix"]} {item["created_at"]}')
        return 0
    if args.action == "rename":
        changed = store.rename_api_key(args.original_name, args.new_name)
        print("renamed" if changed else "not found")
        return 0 if changed else 1
    if args.action == "delete":
        changed = store.delete_api_key(args.name)
        print("deleted" if changed else "not found")
        return 0 if changed else 1
    return 1


def history(args):
    rows = store.history(limit=args.limit, key=args.key, provider=args.provider, contains=args.contains, since=args.since)
    text = "\n\n".join(format_history(row) for row in rows)
    if not text:
        print("No history.")
        return 0
    if sys.stdout.isatty():
        pager = os.environ.get("PAGER") or shutil.which("less")
        if pager:
            subprocess.run([pager], input=text, text=True)
            return 0
    print(text)
    return 0


def format_history(row):
    body = pretty(row["request_body"])
    return f'[{row["api_key_name"]}][{row["created_at"]}]<{body}>'


def pretty(value):
    try:
        return json.dumps(json.loads(value), ensure_ascii=False, indent=2)
    except Exception:
        return value


def dashboard(args):
    load_env()
    url = URL_FILE.read_text().strip() if URL_FILE.exists() else f'http://{os.environ.get("HOST", "127.0.0.1")}:{os.environ.get("PORT", "8787")}'
    print(f"{url}/dashboard")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="run.sh", add_help=False)
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("serve")
    sub.add_parser("up")
    sub.add_parser("down")
    sub.add_parser("status")
    sub.add_parser("dashboard")
    h = sub.add_parser("history")
    h.add_argument("--key")
    h.add_argument("--provider", choices=["openai", "anthropic"])
    h.add_argument("--contains")
    h.add_argument("--since")
    h.add_argument("--limit", type=int, default=50)
    ak = sub.add_parser("api-key")
    aks = ak.add_subparsers(dest="action")
    gen = aks.add_parser("gen")
    gen.add_argument("name")
    aks.add_parser("list")
    ren = aks.add_parser("rename")
    ren.add_argument("original_name")
    ren.add_argument("new_name")
    dele = aks.add_parser("delete")
    dele.add_argument("name")
    sub.add_parser("help")
    args = parser.parse_args(argv)
    if not args.cmd or args.cmd == "help":
        print_help()
        return 0
    return globals()[args.cmd.replace("-", "_")](args)


def print_help():
    print("""Usage: ./run.sh [command]

Commands:
  ./run.sh
  up
  down
  status
  history [--key name] [--provider openai|anthropic] [--contains text] [--since time] [--limit n]
  api-key gen <name>
  api-key list
  api-key rename <original-name> <new-name>
  api-key delete <name>
  dashboard
  help

API keys are for this capture server. They are accepted by OpenAI and Anthropic compatible endpoints as bearer tokens.
Run ./run.sh with no arguments for a foreground server. Run ./run.sh up for a background server.""")


if __name__ == "__main__":
    raise SystemExit(main())
