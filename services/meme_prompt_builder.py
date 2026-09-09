import logging
import random
from pathlib import Path

logger = logging.getLogger(__name__)

CAPTION_SPLIT_MARKER = "<SPLIT>"

_OUTPUT_CONTRACT = (
    "Если на изображении содержится порнография или обнажённая натура, "
    "верни verdict='REJECTED' и reason='NSFW'. "
    "Не создавай в этом случае подпись. "
    "Во всех остальных случаях верни verdict='OK' и одну цельную подпись в caption. "
    "Подпись должна быть написана на русском языке. "
    f"Для разделения подписи между верхней и нижней частью изображения "
    f"используй маркер {CAPTION_SPLIT_MARKER}. "
    "Если подпись длиннее шести слов, разделение обязательно: "
    f"caption должен содержать ровно один маркер {CAPTION_SPLIT_MARKER}. "
    "Если подпись состоит из шести слов или меньше, разделение необязательно. "
    f"Ставь {CAPTION_SPLIT_MARKER} в естественном смысловом месте. "
    "Текст до и после маркера должен составлять одну цельную мысль. "
    "Строго соблюдай заданную структуру ответа. "
    "Не добавляй Markdown, пояснения, комментарии или другой текст."
)


class MemePromptBuilder:
    def __init__(
        self,
        prompts_dir: Path,
        event_probability: float = 0.1,
        rng: random.Random | None = None,
    ) -> None:
        """Сборщик промптов.

        Args:
            prompts_dir (Path): Директория промптов.
            rng (random.Random | None, optional): Генератор случайных чисел.
                Если не выбран, то используется обычный random.Random.
                Это нужно для тестирования.
        """
        self._prompts_dir = prompts_dir
        self._event_probability = event_probability
        self._rng = rng or random.Random()

        self._validate_directory()

        # base.txt обязательный.
        base_lines = self._read_lines("base.txt")
        self._base = "\n".join(base_lines)

        # Если есть эвенты
        events_path = self._prompts_dir / "events.txt"
        self._events: list[str] = []
        if events_path.is_file():
            # Если есть файл с эвентами, читаем и записываем
            self._events = self._read_lines("events.txt")

        # Поиск файлов вида part1.txt, part2.txt и тд.
        part_paths = [
            path
            for path in self._prompts_dir.glob("part*.txt")
            # Только если это файл и есть порядковый номер.
            if path.is_file() and path.stem[4:].isdecimal()
        ]
        # Сортировка part-файла по его порадковому номеру
        part_paths.sort(key=lambda path: int(path.stem[4:]))

        # Читаем каждый parts и записываем в список list[list[str]]
        self._parts = [self._read_lines(path.name) for path in part_paths]

        logger.info(
            "Prompt set loaded: directory=%s, parts=%d",
            self._prompts_dir,
            len(self._parts),
        )

    def build(self) -> str:

        # Проходимся по каждому parts и берем из них по одному варианту промпта.
        # По сути собираем рецепт промпта из разных кусочков.
        recipe = [self._rng.choice(variants) for variants in self._parts]

        if self._events and self._rng.random() < self._event_probability:
            recipe.append(self._rng.choice(self._events))

        blocks = [
            f"## Обязательные правила\n{_OUTPUT_CONTRACT}",
            f"## Базовые инструкции\n{self._base}",
        ]

        if recipe:
            conditions = "\n".join(
                f"Условие {num}: {item}" for num, item in enumerate(recipe, start=1)
            )

            blocks.append(
                "## Условия этой генерации\n"
                "Все условия относятся к одной подписи. "
                "Примени их совместно, не отвечай на каждое отдельно.\n"
                f"{conditions}"
            )

        blocks.append(
            "## Задача\n"
            "Создай одну мем-подпись к переданному изображению, "
            "если это разрешено обязательными правилами. "
            "При противоречии инструкций приоритет имеют обязательные правила."
        )

        # Теперь жойним все блоки в строку
        return "\n\n".join(blocks)

    def _validate_directory(self) -> None:
        """Валидирует директорию с промптами.

        Raises:
            ValueError: Если директория некорректна
                или отсутствует обязательный base.txt
        """
        if not self._prompts_dir.is_dir():
            # Если указаная промпт-директория не директория
            raise ValueError(f"Prompts directory does not exist: {self._prompts_dir}")
        if not (self._prompts_dir / "base.txt").is_file():
            # Если base.txt не файл
            raise ValueError(
                f"Required prompt file missing: {self._prompts_dir / 'base.txt'}"
            )

    def _read_lines(self, filename: str) -> list[str]:
        """Читает содержимое промпт-файла построчно.

        Args:
            filename (str): Имя файла.

        Raises:
            ValueError: Если файл не содержит ни одной промпт-строки.

        Returns:
            list[str]: Список промпт-строк.
        """

        path = self._prompts_dir / filename

        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()

        items: list[str] = []

        for line in lines:
            # Пропускаем пустые строки и строки комментариев
            if not line.strip() or self._is_comment(line):
                continue

            items.append(line.strip())

        if not items:
            raise ValueError(f"Prompt file contains no entries: {path}")

        return items

    @staticmethod
    def _is_comment(line: str) -> bool:
        return line.lstrip().startswith("#")
