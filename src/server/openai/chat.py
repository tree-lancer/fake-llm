import time


def extract_message(payload):
    messages = payload.get("messages") or []
    texts = []
    for message in messages:
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, str):
            texts.append(content)
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("text"):
                    texts.append(part["text"])
    return "\n".join(texts)


def response(payload, text):
    return {
        "id": "chatcmpl_fake",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": payload.get("model", "fake-model"),
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }


def stream_events(payload, text):
    created = int(time.time())
    model = payload.get("model", "fake-model")
    return [
        (
            "message",
            {
                "id": "chatcmpl_fake",
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}],
            },
        ),
        (
            "message",
            {
                "id": "chatcmpl_fake",
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [{"index": 0, "delta": {"content": text}, "finish_reason": None}],
            },
        ),
        (
            "message",
            {
                "id": "chatcmpl_fake",
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            },
        ),
    ]
