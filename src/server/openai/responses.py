import time


def extract_message(payload):
    value = payload.get("input", "")
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            content = item.get("content") if isinstance(item, dict) else None
            if isinstance(content, str):
                parts.append(content)
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict):
                        text = part.get("text") or part.get("input_text")
                        if text:
                            parts.append(text)
        return "\n".join(parts)
    return ""


def response(payload, text):
    return {
        "id": "resp_fake",
        "object": "response",
        "created_at": int(time.time()),
        "status": "completed",
        "model": payload.get("model", "fake-model"),
        "output": [
            {
                "id": "msg_fake",
                "type": "message",
                "status": "completed",
                "role": "assistant",
                "content": [{"type": "output_text", "text": text}],
            }
        ],
        "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
    }


def stream_events(payload, text):
    full = response(payload, text)
    item = full["output"][0]
    part = item["content"][0]
    started = {**full, "status": "in_progress", "output": []}
    return [
        ("response.created", {"type": "response.created", "response": started}),
        ("response.output_item.added", {"type": "response.output_item.added", "output_index": 0, "item": {**item, "content": []}}),
        ("response.content_part.added", {"type": "response.content_part.added", "item_id": item["id"], "output_index": 0, "content_index": 0, "part": {**part, "text": ""}}),
        ("response.output_text.delta", {"type": "response.output_text.delta", "item_id": item["id"], "output_index": 0, "content_index": 0, "delta": text}),
        ("response.output_text.done", {"type": "response.output_text.done", "item_id": item["id"], "output_index": 0, "content_index": 0, "text": text}),
        ("response.content_part.done", {"type": "response.content_part.done", "item_id": item["id"], "output_index": 0, "content_index": 0, "part": part}),
        ("response.output_item.done", {"type": "response.output_item.done", "output_index": 0, "item": item}),
        ("response.completed", {"type": "response.completed", "response": full}),
    ]
