#!/bin/bash

# Обновление и установка необходимых пакетов
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git

# Клонирование репозитория вашего приложения
git clone https://github.com/yourusername/yourrepository.git
cd yourrepository

# Создание и активация виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
export FLASK_APP=run.py
export FLASK_ENV=production

# Запуск миграций базы данных
flask db upgrade

# Создание systemd службы
SERVICE_FILE=/etc/systemd/system/myflaskapp.service

sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=My Flask App
After=network.target

[Service]
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
ExecStart=$(pwd)/venv/bin/flask run --host=0.0.0.0 --port=8000

[Install]
WantedBy=multi-user.target
EOL

# Перезагрузка systemd и запуск службы
sudo systemctl daemon-reload
sudo systemctl enable myflaskapp.service
sudo systemctl start myflaskapp.service