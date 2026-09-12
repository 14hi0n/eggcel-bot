import re
from collections.abc import Mapping


class PromptTemplateRenderer:
    _token = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")

    def render(
        self,
        row_text: str,
        values: Mapping[str, str | None],
    ) -> str | None:
        """Подставляет значения в шаблон текста.

        Args:
            row_text (str): Исходный текст с шаблонами вида {{ name }}.
            values (Mapping[str, str  |  None]): Сопостовление имен шаблонов
                с их значениями.

        Returns:
            str | None: Текст с подставленными значениями или None,
                если для одного из используемых шаблонов отсутствует значение.
        """
        names = set()

        for name in self._token.findall(row_text):
            names.add(name.lower())

        unknown = names - values.keys()

        if unknown:
            raise ValueError(f"Unknown placeholder: {sorted(unknown)}")

        for name in values:
            if not values[name]:
                return None

        result = self._token.sub(
            lambda match: values[match.group(1).lower()] or "", row_text
        )

        return result
