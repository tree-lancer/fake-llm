import json
import unittest

from src.server.anthropic.messages import response
from src.server.app import bearer
from src.server.strategy import load_strategy


class StructuredRepliesTest(unittest.TestCase):
    def test_anthropic_api_key_header(self):
        self.assertEqual(bearer({"x-api-key": "mock-key"}), "mock-key")
        self.assertEqual(bearer({"Authorization": "Bearer mock-key"}), "mock-key")

    def test_forced_tool_reply(self):
        payload = {"model": "fake", "tools": [{"name": "respond"}], "tool_choice": {"type": "tool", "name": "respond"}}
        message = response(payload, '{"answer": 1}')
        self.assertEqual(message["content"][0]["type"], "tool_use")
        self.assertEqual(message["content"][0]["input"], {"answer": 1})

    def test_schema_stub(self):
        schema = {"type": "object", "properties": {"value": {"type": "array", "prefixItems": [{"type": "integer"}, {"type": "string"}]}}, "required": ["value"]}
        answer = load_strategy("schema_stub").reply(None, "", {"endpoint": "chat.completions", "payload": {"response_format": {"json_schema": {"schema": schema}}}})
        self.assertEqual(json.loads(answer), {"value": [1, "example"]})


if __name__ == "__main__":
    unittest.main()
