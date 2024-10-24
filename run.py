from app import app, db
from app.models import User, Note, ListItem, Reminder

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Создает таблицы заново
    app.run(debug=True, port=8000)  # Запуск на порту 8000