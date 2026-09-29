class GenerationChatNotFoundError(LookupError):
    def __init__(self, telegram_chat_id: int) -> None:
        self.telegram_chat_id = telegram_chat_id
        super().__init__(f"Chat {telegram_chat_id} is not registered")


class GenerationUserNotFoundError(LookupError):
    def __init__(self, telegram_user_id: int) -> None:
        self.telegram_user_id = telegram_user_id
        super().__init__(f"User {telegram_user_id} is not registered")
