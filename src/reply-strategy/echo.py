from common.base import ReplyStrategy


class Strategy(ReplyStrategy):
    name = "echo"

    def reply(self, api_key, message, context):
        return message or ""
