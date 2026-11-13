# Размещение задания 4 на PythonAnywhere

1. Откройте Bash Console. Клонируйте опубликованный репозиторий и выберите версию `lab-04`:

   ```bash
   git clone https://github.com/LocoSan/internet-resources-health.git health-journal
   cd health-journal
   git switch --detach lab-04
   python3.12 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py collectstatic --noinput
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

2. Во вкладке **Web** добавьте приложение через **Manual configuration → Python 3.12**. Укажите виртуальное окружение `/home/USERNAME/health-journal/.venv`. В файле WSGI на вкладке **Web** установите:

   ```python
   import os
   import sys

   sys.path.insert(0, "/home/USERNAME/health-journal")
   os.environ["DJANGO_SETTINGS_MODULE"] = "health.settings"
   os.environ["DJANGO_DEBUG"] = "0"
   os.environ["DJANGO_SECRET_KEY"] = "ЗАМЕНИТЕ_НА_СГЕНЕРИРОВАННЫЙ_КЛЮЧ"
   os.environ["DJANGO_ALLOWED_HOSTS"] = "USERNAME.pythonanywhere.com"

   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```

   Замените `USERNAME` и домен на свои. Не добавляйте WSGI с ключом в Git.

3. Добавьте в **Static files** маршрут `/static/` → `/home/USERNAME/health-journal/staticfiles`. Нажмите **Reload**, откройте выданный HTTPS-адрес. Проверьте ввод, поиск и изменение записи. Для публичного показа используйте только вымышленные данные.
