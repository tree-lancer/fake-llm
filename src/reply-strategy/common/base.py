from abc import ABC, abstractmethod


class ReplyStrategy(ABC):
    name = "base"

    @abstractmethod
    def reply(self, api_key, message, context):
        raise NotImplementedError
