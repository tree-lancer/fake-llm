import html
import json

from src.db.store import export_rows


def render():
    rows = export_rows()
    items = "\n".join(render_row(row) for row in rows)
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>What Was Sent To AI</title>
<style>
body{{background:#003366;color:#000;font-family:Verdana,Arial,sans-serif;font-size:12px;margin:0}}
table{{border-collapse:collapse}}
a{{color:#0000ee}}
.top{{background:#c0c0c0;border-bottom:3px ridge #fff;padding:6px 8px;font-weight:bold}}
.wrap{{width:960px;margin:12px auto;background:#dcdcdc;border:4px ridge #fff}}
.bar{{background:#000080;color:#fff;padding:4px 6px;font-weight:bold}}
.room{{height:560px;overflow:auto;background:#fff;border:2px inset #808080;margin:8px;padding:6px}}
.msg{{border-bottom:1px dotted #999;padding:5px 3px}}
.meta{{color:#800000;font-weight:bold}}
.body{{white-space:pre-wrap;font-family:"Courier New",monospace;margin-top:3px}}
.reply{{color:#006000;margin-top:3px}}
.side{{background:#ffffcc;border:2px inset #808080;margin:8px;padding:6px}}
input{{font-family:Verdana,Arial,sans-serif;font-size:12px}}
</style>
<meta http-equiv="refresh" content="8">
</head>
<body>
<div class="top">What Was Sent To AI - Capture Chat</div>
<div class="wrap">
<div class="bar">Lobby</div>
<div class="side">Auto refresh is on. Newest messages appear first.</div>
<div class="room">{items or '<div class="msg">No captures yet.</div>'}</div>
</div>
</body>
</html>"""


def render_row(row):
    body = pretty(row["request_body"])
    reply = pretty(row["response_body"])
    meta = f'[{html.escape(row["api_key_name"] or "unknown")}][{html.escape(row["created_at"])}][{html.escape(row["provider"])}:{html.escape(row["endpoint"])}]'
    return f'<div class="msg"><div class="meta">{meta}</div><div class="body">{html.escape(body)}</div><div class="reply">reply: {html.escape(reply)}</div></div>'


def pretty(value):
    try:
        return json.dumps(json.loads(value), ensure_ascii=False, indent=2)
    except Exception:
        return value
