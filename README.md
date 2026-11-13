# Журнал показателей здоровья

Вариант 9, задания 3–5. Эта версия: задание 5, хранение в JSON и PostgreSQL в Docker.

| Версия | Что можно показать |
|---|---|
| `lab-03` | Ввод, проверка, загрузка и выгрузка файлов JSON |
| `lab-04` | JSON и SQLite, дубликаты, поиск, изменение, удаление; [размещение](DEPLOY.md) |
| `lab-05` | Те же операции в Docker с PostgreSQL, перенос данных из SQLite |

Для просмотра старой версии: `git switch --detach lab-03` или `git switch --detach lab-04`. Назад: `git switch main`.

## Запуск без Docker

В PowerShell из папки проекта:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8003
```

Открыть http://127.0.0.1:8003/. Для проверки импорта загрузить `examples/measurements.json`. Локально используется SQLite. Повтором считается совпадение всех четырёх полей. Поиск, изменение и удаление доступны на вкладке «База данных».

Проверка: `python manage.py test` из виртуального окружения.

## Запуск в Docker для разработки

```powershell
Copy-Item .env.example .env
docker compose up --build --wait
```

В Linux вместо `Copy-Item`: `cp .env.example .env`. Открыть http://127.0.0.1:8003/. Приложение само применяет миграции и собирает статические файлы. После изменения кода повторить `docker compose up --build --wait`. Проверка на PostgreSQL: `docker compose exec web python manage.py test`.

Остановить: `docker compose down`. Данные PostgreSQL и JSON и собранная статика остаются в отдельных volumes. Команда `docker compose down --volumes` удаляет эти данные.

## Перенос данных из задания 4

Остановите старое приложение и сохраните копию его `db.sqlite3`. Для PythonAnywhere скачайте файл базы через вкладку **Files**. Далее выполните в папке новой версии:

```powershell
docker compose up --build --wait
docker compose cp ./db.sqlite3 web:/tmp/old.sqlite3
docker compose exec web python manage.py import_sqlite /tmp/old.sqlite3
```

Команда показывает количество добавленных и уже существовавших записей. Проверьте перенесённые строки на вкладке «База данных». При повторном переносе одинаковые записи пропускаются. Если нужно сохранить JSON, скопируйте файлы старого каталога `data` в новый контейнер: `docker compose cp ./data/. web:/app/data/`.

## Запуск на сервере

1. Создайте `.env` из примера. Замените `DJANGO_SECRET_KEY` и `POSTGRES_PASSWORD` случайными значениями; можно получить их командой `python -c "import secrets; print(secrets.token_hex(32))"` по одному на каждый параметр. Не сохраняйте реальные значения в Git.
2. Установите `DJANGO_DEBUG=0` и `DJANGO_ALLOWED_HOSTS=127.0.0.1,ваш-домен`. Для HTTPS через доверенный обратный прокси установите `DJANGO_TRUST_PROXY=1` и `DJANGO_SECURE_COOKIES=1`.
3. Запустите `docker compose up -d --build --wait`. Настройте HTTPS-прокси на `127.0.0.1:8003`, передавая исходный Host и свой заголовок X-Forwarded-Proto. PostgreSQL доступен только внутри Docker-сети.
