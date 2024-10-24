import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    YANDEX_CLIENT_ID = '686d26571d284e249606165535c71c89'
    YANDEX_CLIENT_SECRET = 'd4cb9804ab0c4ec6a705ddcfcaa0e513'
    YANDEX_REDIRECT_URI = 'http://localhost:5000/callback'
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # Устанавливаем максимальный размер файла в 100 МБ
    ALLOWED_EXTENSIONS = set()  # Пустое множество, разрешаем все типы файлов
