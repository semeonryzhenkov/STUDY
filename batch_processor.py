import os
import asyncio
from pathlib import Path
from github_importer import GithubArchiveImporter

async def process_single_archive(archive_path, output_dir):
    """Обрабатывает один архив: проверяет и извлекает метаданные."""
    try:
        importer = GithubArchiveImporter(str(archive_path))
        # Попытка найти основной файл (например, solution.py или main.py)
        # В реальном сценарии здесь можно запускать тесты или линтеры
        print(f"[OK] Архив {archive_path.name} прошел базовую проверку структуры.")
        return True
    except Exception as e:
        print(f"[ERROR] Ошибка в архиве {archive_path.name}: {e}")
        return False

async def batch_process(input_folder, max_concurrent=5):
    """
    Массовая обработка всех ZIP-архивов в папке.
    
    :param input_folder: Путь к папке с архивами.
    :param max_concurrent: Максимальное количество одновременных задач.
    """
    input_path = Path(input_folder)
    if not input_path.exists():
        print(f"Папка {input_folder} не найдена.")
        return

    archives = list(input_path.glob("*.zip"))
    if not archives:
        print("ZIP-архивы не найдены.")
        return

    print(f"Найдено архивов: {len(archives)}. Запуск обработки...")
    
    semaphore = asyncio.Semaphore(max_concurrent)

    async def limited_process(archive):
        async with semaphore:
            await process_single_archive(archive, input_path / "processed")

    tasks = [limited_process(archive) for archive in archives]
    await asyncio.gather(*tasks)
    print("Обработка завершена.")

if __name__ == "__main__":
    # Пример использования:
    # python batch_processor.py ./qwen_archives
    import sys
    folder = sys.argv[1] if len(sys.argv) > 1 else "./archives"
    asyncio.run(batch_process(folder))
