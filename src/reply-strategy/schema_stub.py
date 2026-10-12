"""Generate a deterministic JSON example from a requested output schema."""

import json

from common.base import ReplyStrategy


def example(schema):
    if "enum" in schema:
        return schema["enum"][0]
    if "anyOf" in schema:
        choices = schema["anyOf"]
        non_null = next((item for item in choices if item.get("type") != "null"), choices[0])
        return example(non_null)
    kind = schema.get("type")
    if kind == "object":
        properties = schema.get("properties") or {}
        return {name: example(field) for name, field in properties.items() if name in schema.get("required", ())}
    if kind == "array":
        if "prefixItems" in schema:
            return [example(item) for item in schema["prefixItems"]]
        return [example(schema["items"])] if "items" in schema and schema.get("minItems", 0) > 0 else []
    return {"integer": 1, "number": 1.5, "string": "example", "boolean": True, "null": None}.get(kind, None)


class Strategy(ReplyStrategy):
    name = "schema_stub"

    def reply(self, api_key, message, context):
        payload = context["payload"]
        if context["endpoint"] == "chat.completions":
            schema = ((payload.get("response_format") or {}).get("json_schema") or {}).get("schema")
        elif context["endpoint"] == "messages":
            schema = next((tool.get("input_schema") for tool in payload.get("tools", []) if tool.get("name") == (payload.get("tool_choice") or {}).get("name")), None)
        else:
            schema = None
        return json.dumps(example(schema or {"type": "object"}))
