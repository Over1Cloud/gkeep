from app import app, db, login_manager
from flask import request, redirect, url_for
from flask_login import login_user, logout_user, current_user
from app.models import User
import requests
import logging

logger = logging.getLogger(__name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    auth_url = (
        f"https://oauth.yandex.ru/authorize?"
        f"response_type=code"
        f"&client_id={app.config['YANDEX_CLIENT_ID']}"
        f"&redirect_uri={app.config['YANDEX_REDIRECT_URI']}"
        f"&scope=login:info+login:email"
    )
    return redirect(auth_url)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        logger.error("Authorization code not received")
        return 'Ошибка авторизации', 400

    token_url = 'https://oauth.yandex.ru/token'
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': app.config['YANDEX_CLIENT_ID'],
        'client_secret': app.config['YANDEX_CLIENT_SECRET'],
        'redirect_uri': app.config['YANDEX_REDIRECT_URI']
    }
    response = requests.post(token_url, data=data)
    token_data = response.json()

    logger.debug(f"Token response: {token_data}")

    if 'access_token' not in token_data:
        logger.error(f"Failed to get access token. Response: {token_data}")
        return 'Ошибка получения токена', 400

    access_token = token_data['access_token']
    user_info_url = 'https://login.yandex.ru/info'
    headers = {'Authorization': f'OAuth {access_token}'}
    user_info_response = requests.get(user_info_url, headers=headers)
    user_info = user_info_response.json()

    user = User.query.filter_by(username=user_info['login']).first()
    if not user:
        user = User(
            username=user_info['login'],
            email=user_info.get('default_email'),
            first_name=user_info.get('first_name'),
            last_name=user_info.get('last_name'),
            phone=user_info.get('default_phone', {}).get('number'),
            birthday=user_info.get('birthday')
        )
        db.session.add(user)
        db.session.commit()

    login_user(user)
    return redirect(url_for('index'))
