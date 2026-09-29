class AdminHelpMessages:
    @classmethod
    def help(cls) -> str:
        return cls._render()

    @staticmethod
    def _render() -> str:
        return "\n".join(
            (
                "/add <chat_id> - одобрить чат",
                "/remove <chat_id> - отклонить чат",
                "/pending - список чатов ожидающих модерацию",
                "/stat - общая статистика генераций",
                "/stat h - подробнее про команду",
                "/ver - текущая версия бота",
            )
        )
