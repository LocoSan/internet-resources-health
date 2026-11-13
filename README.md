# Журнал показателей здоровья

Вариант 9, задания 3–5. Эта версия: задание 3, хранение в JSON.

## Запуск

В PowerShell из папки проекта:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8003
```

Открыть http://127.0.0.1:8003/. Для проверки импорта загрузить `examples/measurements.json`. Форма принимает имя учебной карточки, дату, пульс и температуру. Все файлы сохраняются в `data/`; ссылка выгрузки скачивает общий JSON.

Проверка: `python manage.py test` из виртуального окружения.
