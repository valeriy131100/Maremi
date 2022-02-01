
class ChatNotAllowed(Exception):
    def __init__(self, chat_id):
        self.chat_id = chat_id
