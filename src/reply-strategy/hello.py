from common.base import ReplyStrategy


class Strategy(ReplyStrategy):
    name = "hello"

    def reply(self, api_key, message, context):
        return "Hello"
