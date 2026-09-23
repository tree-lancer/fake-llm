def extract_message(payload):
    messages = payload.get("messages") or []
    texts = []
    for message in messages:
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, str):
            texts.append(content)
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict):
                    text = part.get("text")
                    if text:
                        texts.append(text)
    return "\n".join(texts)


def response(payload, text):
    return {
        "id": "msg_fake",
        "type": "message",
        "role": "assistant",
        "model": payload.get("model", "fake-model"),
        "content": [{"type": "text", "text": text}],
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {"input_tokens": 0, "output_tokens": 0},
    }
