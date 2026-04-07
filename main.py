import os
import sys
import importlib.util

def load_module_from_file(file_path, module_name):
    """Загружает модуль из .py файла."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Не удалось загрузить спецификацию для {file_path}")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def main():
    # Папка, где лежит код от Qwen (по умолчанию 'qwen_code')
    target_folder = "qwen_code"
    
    if not os.path.exists(target_folder):
        print(f"Ошибка: Папка '{target_folder}' не найдена.")
        print(f"Создайте папку '{target_folder}' и положите туда ваши .py файлы (например, solution.py).")
        return

    py_files = [f for f in os.listdir(target_folder) if f.endswith('.py')]
    
    if not py_files:
        print(f"В папке '{target_folder}' не найдено файлов .py")
        return

    print(f"Найдено файлов: {len(py_files)}. Начинаю обработку...\n")

    for filename in py_files:
        file_path = os.path.join(target_folder, filename)
        module_name = filename[:-3]  # Убираем .py
        
        try:
            print(f"-> Импорт модуля: {filename}...")
            module = load_module_from_file(file_path, module_name)
            
            # Попытка найти и запустить основную функцию (если есть)
            if hasattr(module, 'solve'):
                print(f"   Запуск функции solve()...")
                result = module.solve()
                print(f"   Результат: {result}")
            elif hasattr(module, 'main'):
                print(f"   Запуск функции main()...")
                module.main()
            else:
                print(f"   Успешно загружен. (Нет функций solve() или main() для автозапуска)")
                
        except Exception as e:
            print(f"   Ошибка при обработке {filename}: {e}")
        
        print("-" * 30)

    print("Обработка завершена.")

if __name__ == "__main__":
    main()
