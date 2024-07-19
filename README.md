# Создать новое виртуальное окружение:

python -m venv .venv

# Активация окружения:

.venv\Scripts\activate

# Установка зависимостей:

pip install -r requirements.txt



daphne -b 127.0.0.1 -p 8000 dev.asgi:application
