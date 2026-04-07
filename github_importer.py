"""
Github Importer Module
Стабильный импорт кода из архива (например, сгенерированного агентом).
"""

import os
import sys
import importlib.util
import tempfile
import shutil
import zipfile
import urllib.request
from pathlib import Path
from typing import Optional, Dict, Any


class GithubArchiveImporter:
    """
    Класс для безопасного импорта модулей из ZIP-архива.
    Подходит для загрузки кода от агентов (QwenCoder и др.).
    """

    def __init__(self, archive_path: Optional[str] = None, cleanup: bool = True):
        """
        :param archive_path: Путь к локальному ZIP-файлу или URL.
        :param cleanup: Удалять ли временные файлы после импорта (по умолчанию True).
        """
        self.archive_source = archive_path
        self.cleanup = cleanup
        self.temp_dir: Optional[str] = None
        self.imported_modules: Dict[str, Any] = {}

    def _download_if_url(self, source: str) -> str:
        """Если передан URL, скачивает файл во временную директорию."""
        if source.startswith(('http://', 'https://')):
            temp_fd, temp_path = tempfile.mkstemp(suffix='.zip')
            try:
                print(f"⬇️ Скачивание архива из: {source}")
                urllib.request.urlretrieve(source, temp_path)
                return temp_path
            except Exception as e:
                os.close(temp_fd)
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise RuntimeError(f"Ошибка скачивания: {e}")
        else:
            if not os.path.exists(source):
                raise FileNotFoundError(f"Архив не найден: {source}")
            return source

    def _extract_archive(self, archive_path: str) -> str:
        """Распаковывает архив во временную директорию."""
        self.temp_dir = tempfile.mkdtemp(prefix='gh_import_')
        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                # Проверка на вредоносные пути (Zip Slip)
                for member in zip_ref.namelist():
                    member_path = os.path.join(self.temp_dir, member)
                    if not os.path.realpath(member_path).startswith(os.path.realpath(self.temp_dir)):
                        raise ValueError(f"Обнаружен опасный путь в архиве: {member}")
                
                zip_ref.extractall(self.temp_dir)
            print(f"📂 Архив распакован в: {self.temp_dir}")
            return self.temp_dir
        except Exception as e:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            raise RuntimeError(f"Ошибка распаковки: {e}")

    def import_module_from_path(self, module_name: str, relative_path: str) -> Any:
        """
        Импортирует конкретный модуль из распакованной директории.
        
        :param module_name: Имя модуля для импорта (как в коде).
        :param relative_path: Относительный путь к файлу .py внутри архива.
        :return: Объект модуля.
        """
        if not self.temp_dir:
            raise RuntimeError("Сначала необходимо загрузить и распаковать архив.")

        module_path = os.path.join(self.temp_dir, relative_path)
        
        if not os.path.exists(module_path):
            raise FileNotFoundError(f"Файл модуля не найден в архиве: {relative_path}")

        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Не удалось создать спецификацию для модуля: {module_name}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module  # Регистрируем в sys.modules
        self.imported_modules[module_name] = module
        
        try:
            spec.loader.exec_module(module)
            print(f"✅ Модуль '{module_name}' успешно импортирован.")
            return module
        except Exception as e:
            del sys.modules[module_name]
            raise ImportError(f"Ошибка выполнения модуля {module_name}: {e}")

    def load_and_import(self, target_file: str, module_name: str = "agent_code") -> Any:
        """
        Полный цикл: скачивание (если нужно) -> распаковка -> импорт.
        
        :param target_file: Путь к файлу внутри архива (например, 'main.py' или 'src/code.py').
        :param module_name: Имя, под которым модуль будет доступен.
        """
        archive_path = self._download_if_url(self.archive_source)
        self._extract_archive(archive_path)
        
        module = self.import_module_from_path(module_name, target_file)
        
        if self.cleanup and self.temp_dir:
            # Опционально: можно оставить файлы для отладки, установив cleanup=False
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            self.temp_dir = None
            
        return module

    def __del__(self):
        """Гарантированная очистка при уничтожении объекта, если включено."""
        if self.cleanup and self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)


# Пример использования (можно раскомментировать для теста)
if __name__ == "__main__":
    # Сценарий 1: Импорт из локального архива
    # Создадим тестовый архив для демонстрации
    test_dir = "test_agent_code"
    os.makedirs(test_dir, exist_ok=True)
    with open(os.path.join(test_dir, "logic.py"), "w", encoding="utf-8") as f:
        f.write("def calculate():\n    return 42\n")
    
    shutil.make_archive("agent_bundle", 'zip', test_dir)
    
    try:
        importer = GithubArchiveImporter(archive_path="agent_bundle.zip", cleanup=True)
        # Импортируем файл logic.py из корня архива как модуль 'dynamic_logic'
        mod = importer.load_and_import(target_file="logic.py", module_name="dynamic_logic")
        
        result = mod.calculate()
        print(f"Результат работы импортированного кода: {result}")
        
    finally:
        # Уборка тестовых файлов
        if os.path.exists("agent_bundle.zip"): os.remove("agent_bundle.zip")
        if os.path.exists(test_dir): shutil.rmtree(test_dir)
