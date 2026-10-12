import json


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
    tool_choice = payload.get("tool_choice") or {}
    tools = payload.get("tools") or []
    chosen = tool_choice.get("name") if tool_choice.get("type") == "tool" else None
    if chosen and any(tool.get("name") == chosen for tool in tools):
        try:
            tool_input = json.loads(text)
        except (TypeError, json.JSONDecodeError):
            tool_input = None
        if isinstance(tool_input, dict):
            return {
                "id": "msg_fake",
                "type": "message",
                "role": "assistant",
                "model": payload.get("model", "fake-model"),
                "content": [{"type": "tool_use", "id": "toolu_fake", "name": chosen, "input": tool_input}],
                "stop_reason": "tool_use",
                "stop_sequence": None,
                "usage": {"input_tokens": 0, "output_tokens": 0},
            }
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
