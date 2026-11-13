# Журнал показателей здоровья

Вариант 9, задания 3–5. Эта версия: задание 4, хранение в JSON и SQLite.

Версия только с файлами: `git switch --detach lab-03`.

## Запуск

В PowerShell из папки проекта:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8003
```

Открыть http://127.0.0.1:8003/. Для проверки импорта загрузить `examples/measurements.json`. Запись можно сохранить в `data/` или в SQLite. Повтором считается совпадение всех четырёх полей. Поиск, изменение и удаление доступны на вкладке «База данных».

Проверка: `python manage.py test` из виртуального окружения.

Размещение: [PythonAnywhere](DEPLOY.md).
