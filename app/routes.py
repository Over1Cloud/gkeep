from flask import render_template, redirect, url_for, request, jsonify, session, current_app, send_from_directory, abort, send_file, flash
from flask_login import login_required, current_user, logout_user
from app import app, db, login_manager
from app.models import Note, ListItem, User, Reminder, Attachment, MonthInfo
import json
import os
from werkzeug.utils import secure_filename
import logging
from datetime import datetime
import shutil
from sqlalchemy.orm import joinedload
import zipfile
import tempfile
from pytz import timezone
import re

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@app.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'updated_at')
    order = request.args.get('order', 'desc')
    
    notes_query = Note.query.filter_by(user_id=current_user.id, is_archived=False)
    
    if sort == 'title':
        notes_query = notes_query.order_by(Note.title.asc() if order == 'asc' else Note.title.desc())
    elif sort == 'created_at':
        notes_query = notes_query.order_by(Note.created_at.asc() if order == 'asc' else Note.created_at.desc())
    else:  # default: updated_at
        notes_query = notes_query.order_by(Note.updated_at.asc() if order == 'asc' else Note.updated_at.desc())
    
    notes = notes_query.paginate(page=page, per_page=20, error_out=False)
    return render_template('index.html', notes=notes, sort=sort, order=order)

@app.route('/note', methods=['POST'])
@login_required
def create_note():
    data = request.json
    new_note = Note(
        title=data.get('title', ''),
        content=data.get('content', ''),
        user_id=current_user.id
    )
    db.session.add(new_note)
    db.session.commit()
    return jsonify({'success': True, 'id': new_note.id})

@app.route('/note/<int:note_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def note_operations(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        abort(403)
    
    if request.method == 'GET':
        # Проверяем наличие файлов вложений
        valid_attachments = []
        for attachment in note.attachments:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], str(note.id), attachment.filename)
            if os.path.exists(file_path):
                valid_attachments.append(attachment)
            else:
                db.session.delete(attachment)
        
        db.session.commit()
        note.attachments = valid_attachments
        return render_template('note.html', note=note)
    
    elif request.method == 'PUT':
        data = request.json
        note.title = data.get('title', note.title)
        note.content = data.get('content', note.content)
        note.color = data.get('color', note.color)
        note.is_list = data.get('is_list', note.is_list)
        
        # Обработка изображения
        temp_image_path = data.get('temp_image_path')
        if temp_image_path:
            filename = os.path.basename(temp_image_path)
            permanent_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(note.id))
            os.makedirs(permanent_folder, exist_ok=True)
            permanent_path = os.path.join(permanent_folder, filename)
            shutil.move(temp_image_path, permanent_path)
            note.image_url = url_for('static', filename=f'uploads/{note.id}/{filename}', _external=True)
        
        if note.is_list:
            ListItem.query.filter_by(note_id=note.id).delete()
            for item in data.get('list_items', []):
                list_item = ListItem(content=item['content'], is_checked=item['is_checked'], note_id=note.id, order=item['order'])
                db.session.add(list_item)
        
        db.session.commit()
        
        msk_time = note.get_msk_updated_at()
        formatted_time = msk_time.strftime('%d.%m.%Y %H:%M')
        
        return jsonify({
            'success': True, 
            'id': note.id, 
            'updated_at': note.updated_at.isoformat() + 'Z',
            'formatted_time': formatted_time
        })
    elif request.method == 'DELETE':
        db.session.delete(note)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Заметка успешно удалена'})

@app.route('/upload_image', methods=['POST'])
@login_required
def upload_image():
    print("Получен запрос на загрузку изображения")
    if 'file' not in request.files:
        print("Файл не найден в запросе")
        return jsonify({'success': False, 'error': 'Файл не найден'}), 400
    file = request.files['file']
    note_id = request.form.get('note_id')
    if not note_id:
        print("ID заметки не указан")
        return jsonify({'success': False, 'error': 'ID заметки не указан'}), 400
    
    print(f"Загрузка изображения для заметки {note_id}")
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        print("Нет прав доступа к заметке")
        abort(403)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], str(note.id), filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file.save(file_path)
        
        attachment = Attachment(filename=filename, file_url=f"/static/uploads/{note.id}/{filename}", note=note)
        db.session.add(attachment)
        db.session.commit()
        
        print(f"Изображение успешно загружено: {filename}")
        return jsonify({
            'success': True,
            'file_url': attachment.file_url,
            'filename': attachment.filename,
            'type': 'image'
        })
    print("Недопустимый тип файла")
    return jsonify({'success': False, 'error': 'Недопустимый тип файла'}), 400

@app.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    notes = Note.query.filter(
        (Note.title.contains(query) | Note.content.contains(query)) & 
        (Note.user_id == current_user.id)
    ).all()
    return jsonify([note.to_dict() for note in notes])

@app.route('/archive')
@login_required
def archive():
    notes = Note.query.filter_by(user_id=current_user.id, is_archived=True).all()
    return render_template('archive.html', notes=notes)

@app.route('/settings')
@login_required
def settings():
    notes_count = Note.query.filter_by(user_id=current_user.id).count()
    return render_template('settings.html', user=current_user, notes_count=notes_count)

@app.route('/reminders')
@login_required
def reminders():
    return render_template('reminders.html')

@app.route('/labels')
@login_required
def labels():
    return render_template('labels.html')

@app.route('/trash')
@login_required
def trash():
    return render_template('trash.html')

@app.route('/archive_note/<int:note_id>', methods=['POST'])
@login_required
def archive_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.author != current_user:
        abort(403)
    note.is_archived = True
    db.session.commit()
    return jsonify({'message': 'Note archived successfully'})

@app.route('/copy_note/<int:note_id>', methods=['POST'])
@login_required
def copy_note(note_id):
    original_note = Note.query.get(note_id)
    if original_note and original_note.author == current_user:
        new_note = Note(
            title=f"Копия: {original_note.title}",
            content=original_note.content,
            color=original_note.color,
            image_url=original_note.image_url,
            is_list=original_note.is_list,
            author=current_user
        )
        db.session.add(new_note)
        db.session.commit()
        return jsonify({'message': 'Note copied successfully'})
    return jsonify({'error': 'Note not found or access denied'}), 404

@app.route('/add_reminder', methods=['POST'])
@login_required
def add_reminder():
    data = request.json
    note = Note.query.get(data['note_id'])
    if note and note.author == current_user:
        reminder = Reminder(date=datetime.strptime(data['reminder_date'], '%Y-%m-%d %H:%M'), note=note)
        db.session.add(reminder)
        db.session.commit()
        return jsonify({'message': 'Reminder added successfully'})
    return jsonify({'error': 'Note not found or access denied'}), 404

@app.route('/add_collaborator', methods=['POST'])
@login_required
def add_collaborator():
    data = request.json
    note = Note.query.get(data['note_id'])
    if note and note.author == current_user:
        collaborator = User.query.filter_by(email=data['collaborator_email']).first()
        if collaborator:
            note.collaborators.append(collaborator)
            db.session.commit()
            return jsonify({'message': 'Collaborator added successfully'})
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'error': 'Note not found or access denied'}), 404

@app.route('/upload_file', methods=['POST'])
@login_required
def upload_file():
    print("Получен запрос на загрузку файла")
    if 'file' not in request.files:
        print("Файл не найден в запросе")
        return jsonify({'success': False, 'error': 'Файл не найден'}), 400
    file = request.files['file']
    note_id = request.form.get('note_id')
    if not note_id:
        print("ID заметки не указан")
        return jsonify({'success': False, 'error': 'ID заметки не указан'}), 400
    
    print(f"Загрузка файла для заметки {note_id}")
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        print("Нет прав доступа к заметке")
        abort(403)

    if file and file.filename:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], str(note.id), filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file.save(file_path)
        
        attachment = Attachment(filename=filename, file_url=f"/static/uploads/{note.id}/{filename}", note=note)
        db.session.add(attachment)
        db.session.commit()
        
        print(f"Файл успешно загружен: {filename}")
        return jsonify({
            'success': True,
            'file_url': attachment.file_url,
            'filename': attachment.filename,
            'type': 'file'
        })
    print("Недопустимый файл")
    return jsonify({'success': False, 'error': 'Недопустимый файл'}), 400

def allowed_file(filename):
    return True  # Разрешаем все типы файлов

@app.route('/note/<int:note_id>', methods=['DELETE'])
@login_required
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.author != current_user:
        abort(403)
    db.session.delete(note)
    db.session.commit()
    return jsonify({'message': 'Note deleted successfully'})

@app.route('/note', methods=['GET', 'POST'])
@login_required
def new_note():
    note = {}  # или создайте пустой объект с нужными атрибутами
    return render_template('note.html', note=note)

@app.route('/note/<int:note_id>', methods=['GET'])
@login_required
def view_note(note_id):
    note = Note.query.options(joinedload(Note.list_items)).get_or_404(note_id)
    if note.user_id != current_user.id:
        abort(403)
    return render_template('note.html', note=note)

@app.route('/unarchive_note/<int:note_id>', methods=['POST'])
@login_required
def unarchive_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.author != current_user:
        abort(403)
    note.is_archived = False
    db.session.commit()
    return jsonify({'message': 'Note unarchived successfully'})

@app.route('/note', methods=['POST'])
@app.route('/note/<int:note_id>', methods=['PUT'])
@login_required
def save_note(note_id=None):
    data = request.json
    if note_id:
        note = Note.query.get_or_404(note_id)
        if note.user_id != current_user.id:
            abort(403)
    else:
        note = Note(user_id=current_user.id)
        db.session.add(note)

    note.title = data.get('title', '')
    note.content = data.get('content', '')
    note.color = data.get('color', '#202124')
    note.updated_at = datetime.utcnow()

    try:
        db.session.commit()
        return jsonify(note.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/download/<int:note_id>/<path:filename>')
@login_required
def download_file(note_id, filename):
    note = Note.query.get_or_404(note_id)
    if note.author != current_user:
        abort(403)
    
    note_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], str(note.id))
    return send_from_directory(note_folder, filename, as_attachment=True)

# Добавьте новый маршрут для получения заметок в формате JSON (для AJAX-заросов)
@app.route('/api/notes')
@login_required
def api_notes():
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'updated_at')
    order = request.args.get('order', 'desc')
    
    notes_query = Note.query.filter_by(user_id=current_user.id, is_archived=False)
    
    if sort == 'title':
        notes_query = notes_query.order_by(Note.title.asc() if order == 'asc' else Note.title.desc())
    elif sort == 'created_at':
        notes_query = notes_query.order_by(Note.created_at.asc() if order == 'asc' else Note.created_at.desc())
    else:  # default: updated_at
        notes_query = notes_query.order_by(Note.updated_at.asc() if order == 'asc' else Note.updated_at.desc())
    
    notes = notes_query.paginate(page=page, per_page=20, error_out=False)
    return jsonify({
        'notes': [note.to_dict() for note in notes.items],
        'total': notes.total,
        'pages': notes.pages,
        'current_page': notes.page
    })

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/delete_notes', methods=['POST'])
@login_required
def delete_selected_notes():
    data = request.json
    note_ids = data.get('note_ids', [])
    try:
        notes = Note.query.filter(Note.id.in_(note_ids), Note.user_id == current_user.id).all()
        for note in notes:
            db.session.delete(note)
        db.session.commit()
        print(f"Заметки успешно удалены: {note_ids}")
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка при удалении заметок: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/note/<int:note_id>', methods=['PUT'])
@login_required
def update_note(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        abort(403)
    
    data = request.json
    note.title = data.get('title', note.title)
    note.content = data.get('content', note.content)
    note.color = data.get('color', '#202124')
    note.text_color = data.get('text_color', '#e8eaed')
    
    # Обновляем вложения
    attachments = data.get('attachments', [])
    existing_attachments = {a.file_url: a for a in note.attachments}
    
    for attachment_data in attachments:
        if attachment_data['url'] in existing_attachments:
            # Обновляем существующее вложение
            attachment = existing_attachments[attachment_data['url']]
            attachment.type = attachment_data['type']
        else:
            # Создаем новое вложение
            new_attachment = Attachment(
                filename=os.path.basename(attachment_data['url']),
                file_url=attachment_data['url'],
                note=note
            )
            db.session.add(new_attachment)
    
    # Удаляем вложения, которых нет в полученных данных
    for attachment in note.attachments:
        if attachment.file_url not in [a['url'] for a in attachments]:
            db.session.delete(attachment)
    
    db.session.commit()
    
    msk_time = note.get_msk_updated_at()
    formatted_time = msk_time.strftime('%d.%m.%Y %H:%M')
    
    return jsonify({
        'success': True, 
        'id': note.id, 
        'updated_at': note.updated_at.isoformat() + 'Z',  # UTC время для атрибута datetime
        'formatted_time': formatted_time  # Отформатированное время МСК
    })

@app.route('/archive_notes', methods=['POST'])
@login_required
def archive_notes():
    data = request.json
    note_ids = data.get('note_ids', [])
    try:
        notes = Note.query.filter(Note.id.in_(note_ids), Note.user_id == current_user.id).all()
        for note in notes:
            note.is_archived = True
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/note/<int:note_id>/attachments', methods=['GET'])
@login_required
def get_note_attachments(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        abort(404)  # Возвращаем 404, если заметка не принадлежит текущему пользователю
    attachments = [attachment.to_dict() for attachment in note.attachments]
    return jsonify({'attachments': attachments})

@app.errorhandler(403)
def forbidden_error(error):
    return jsonify({'error': 'У вас нет прав доступа к этой заметке'}), 403

@app.route('/get_info/<string:date_str>')
@login_required
def get_info(date_str):
    try:
        date = datetime.strptime(date_str, '%m.%Y')
        year, month = date.year, date.month

        month_info = MonthInfo.query.filter_by(
            user_id=current_user.id,
            year=year,
            month=month
        ).first()

        if not month_info:
            month_info = MonthInfo(user_id=current_user.id, year=year, month=month)
            db.session.add(month_info)
            db.session.commit()

        hours_data = parse_notes_for_hours(current_user.id, year, month)

        return jsonify({
            'norm_hours': month_info.norm_hours or 0,
            'total_hours': hours_data['total_hours'] + hours_data['work_hours'],
            'night_hours': hours_data['total_night_hours'] + hours_data['night_work_hours'],
            'salary': month_info.salary or 0,
            'advance': month_info.advance or 0
        })
    except Exception as e:
        logger.error(f"Error in get_info: {str(e)}")
        return jsonify({'error': 'Произошла ошибка при получении информации'}), 500

@app.route('/save_info', methods=['POST'])
@login_required
def save_info():
    data = request.json
    year, month = map(int, data['month_year'].split('-'))
    info = MonthInfo.query.filter_by(user_id=current_user.id, year=year, month=month).first()
    if not info:
        info = MonthInfo(user_id=current_user.id, year=year, month=month)
    
    info.norm_hours = data.get('norm_hours')
    info.advance = data.get('advance')
    
    db.session.add(info)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/restore_notes', methods=['POST'])
@login_required
def restore_notes():
    data = request.json
    note_ids = data.get('note_ids', [])
    try:
        notes = Note.query.filter(Note.id.in_(note_ids), Note.user_id == current_user.id).all()
        for note in notes:
            note.is_archived = False
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/export_db')
@login_required
def export_db():
    temp_dir = tempfile.mkdtemp()
    try:
        zip_filename = f"notes_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        zip_path = os.path.join(temp_dir, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            notes = Note.query.filter_by(user_id=current_user.id).all()
            for note in notes:
                note_dir = str(note.id)
                note_data = note.to_dict(include_attachments=True)
                
                # Сохраняем данные заметки в JSON файл
                json_filename = f"{note.id}_note.json"
                json_path = os.path.join(temp_dir, json_filename)
                with open(json_path, 'w', encoding='utf-8') as json_file:
                    json.dump(note_data, json_file, ensure_ascii=False, indent=2)
                zipf.write(json_path, f"{note_dir}/{json_filename}")
                os.remove(json_path)  # Удаляем временный JSON файл
                
                # Добавляем вложения
                for attachment in note.attachments:
                    attachment_path = os.path.join(app.config['UPLOAD_FOLDER'], str(note.id), attachment.filename)
                    if os.path.exists(attachment_path):
                        zipf.write(attachment_path, f"{note_dir}/{attachment.filename}")
        
        return send_file(zip_path, as_attachment=True, download_name=zip_filename, mimetype='application/zip')
    except Exception as e:
        logger.error(f"Ошибка при экспорте базы данных: {str(e)}")
        return jsonify({'error': 'Произошла ошибка при экспорте базы данных'}), 500
    finally:
        # Удаляем временную директорию и все её содержимое
        shutil.rmtree(temp_dir, ignore_errors=True)

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    try:
        # Удаляем все заметки пользователя
        Note.query.filter_by(user_id=current_user.id).delete()
        
        # Удаляем все напоминания пользователя
        Reminder.query.filter_by(user_id=current_user.id).delete()
        
        # Удаляем все информации о месяцах пользователя
        MonthInfo.query.filter_by(user_id=current_user.id).delete()
        
        # Сохраняем ID пользователя перед удалением
        user_id = current_user.id
        
        # Уаляем пользователя
        db.session.delete(current_user)
        db.session.commit()
        
        # Удаляем папку с загруженными файлами пользователя
        user_upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(user_id))
        if os.path.exists(user_upload_folder):
            shutil.rmtree(user_upload_folder)
        
        # Выходим из системы
        logout_user()
        
        flash('Ваш аккаунт был успешно удален.', 'success')
        
        # Перенаправляем на страницу входа
        return redirect(url_for('login'))
    except Exception as e:
        db.session.rollback()
        flash(f'Произошла ошибка при удалении аккаунта: {str(e)}', 'error')
        return redirect(url_for('settings'))

@app.route('/import_db', methods=['POST'])
@login_required
def import_db():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'Файл не найден'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Файл не выбран'}), 400
    if file and file.filename.endswith('.zip'):
        try:
            imported_notes_count = 0
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = os.path.join(temp_dir, 'import.zip')
                file.save(zip_path)
                
                with zipfile.ZipFile(zip_path, 'r') as zipf:
                    for filename in zipf.namelist():
                        if filename.endswith('_note.json'):
                            with zipf.open(filename) as json_file:
                                note_data = json.load(json_file)
                                
                                # Создаем новую заметку
                                new_note = Note(
                                    title=note_data['title'],
                                    content=note_data['content'],
                                    color=note_data['color'],
                                    is_list=note_data['is_list'],
                                    user_id=current_user.id
                                )
                                db.session.add(new_note)
                                db.session.flush()  # Чтобы получить ID новой заметки
                                
                                # Обрабатываем лложения
                                if 'attachments' in note_data:
                                    for attachment_data in note_data['attachments']:
                                        attachment_filename = attachment_data['filename']
                                        attachment_path = os.path.join(str(note_data['id']), attachment_filename)
                                        
                                        if attachment_path in zipf.namelist():
                                            # Извлекаем файл вложения
                                            extracted_path = zipf.extract(attachment_path, temp_dir)
                                            
                                            # Создаем директорию для вложений новой заметки
                                            new_attachment_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(new_note.id))
                                            os.makedirs(new_attachment_dir, exist_ok=True)
                                            
                                            # Перемещаем файл в новую директорию
                                            new_attachment_path = os.path.join(new_attachment_dir, attachment_filename)
                                            os.rename(extracted_path, new_attachment_path)
                                            
                                            # Создаем новое вложение в азе данных
                                            new_attachment = Attachment(
                                                filename=attachment_filename,
                                                file_url=f"/static/uploads/{new_note.id}/{attachment_filename}",
                                                note=new_note
                                            )
                                            db.session.add(new_attachment)
                                
                                imported_notes_count += 1
                
                db.session.commit()
            return jsonify({'success': True, 'imported_notes_count': imported_notes_count})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
    else:
        return jsonify({'success': False, 'error': 'Недопустимый тип файла'}), 400

@app.route('/delete_notes', methods=['POST'])
@login_required
def delete_multiple_notes():
    data = request.json
    note_ids = data.get('note_ids', [])
    try:
        Note.query.filter(Note.id.in_(note_ids), Note.user_id == current_user.id).delete(synchronize_session=False)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/delete_all_archived', methods=['POST'])
@login_required
def delete_all_archived():
    try:
        Note.query.filter_by(user_id=current_user.id, is_archived=True).delete(synchronize_session=False)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/delete_attachment/<int:note_id>/<path:filename>', methods=['DELETE'])
@login_required
def delete_attachment(note_id, filename):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        abort(403)
    
    # Получаем полный путь к файлу
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], str(note_id), filename)
    
    # Проверяем, существует ли файл
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'error': 'Файл не найден'}), 404
    
    try:
        # Удаляем файл
        os.remove(file_path)
        
        # Удаляем запись о вложении из базы данных
        attachment = Attachment.query.filter_by(note_id=note_id, filename=filename).first()
        if attachment:
            db.session.delete(attachment)
            db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/note', methods=['POST'])
@login_required
def create_empty_note():
    new_note = Note(title='', content='', user_id=current_user.id)
    db.session.add(new_note)
    db.session.commit()
    return jsonify({'success': True, 'id': new_note.id})

def parse_notes_for_hours(user_id, year, month):
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    notes = Note.query.filter(
        Note.user_id == user_id,
        Note.created_at >= start_date,
        Note.created_at < end_date
    ).all()

    total_hours = 0
    total_night_hours = 0
    work_hours = 0
    night_work_hours = 0

    for note in notes:
        if 'Н' in note.title:
            match = re.search(r'Общее время: (\d+:\d+)', note.content)
            if match:
                hours, minutes = map(int, match.group(1).split(':'))
                total_hours += hours + minutes / 60

            match = re.search(r'Общее ночное время: (\d+:\d+)', note.content)
            if match:
                hours, minutes = map(int, match.group(1).split(':'))
                total_night_hours += hours + minutes / 60

        elif 'Д' in note.title:
            match = re.search(r'Рабочее время: (\d+:\d+)', note.content)
            if match:
                hours, minutes = map(int, match.group(1).split(':'))
                work_hours += hours + minutes / 60

            match = re.search(r'Ночных часов: (\d+:\d+)', note.content)
            if match:
                hours, minutes = map(int, match.group(1).split(':'))
                night_work_hours += hours + minutes / 60

    return {
        'total_hours': round(total_hours, 2),
        'total_night_hours': round(total_night_hours, 2),
        'work_hours': round(work_hours, 2),
        'night_work_hours': round(night_work_hours, 2)
    }

