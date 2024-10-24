from app import db
from flask_login import UserMixin
from datetime import datetime
import pytz
import os
from flask import url_for

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    phone = db.Column(db.String(20))
    birthday = db.Column(db.String(10))
    notes = db.relationship('Note', backref='author', lazy='dynamic')

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    content = db.Column(db.Text)
    color = db.Column(db.String(7), default='#ffffff')
    is_list = db.Column(db.Boolean, default=False)
    image_url = db.Column(db.String(255))
    file_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    list_items = db.relationship('ListItem', backref='note', lazy=True, cascade='all, delete-orphan')
    reminders = db.relationship('Reminder', backref='note', lazy=True, cascade='all, delete-orphan')
    is_archived = db.Column(db.Boolean, default=False)
    attachments = db.relationship('Attachment', back_populates='note', cascade='all, delete-orphan')

    def get_msk_updated_at(self):
        moscow_tz = pytz.timezone('Europe/Moscow')
        return self.updated_at.replace(tzinfo=pytz.UTC).astimezone(moscow_tz)

    def to_dict(self, include_attachments=False):
        data = {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'color': self.color,
            'is_list': self.is_list,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'file_url': self.file_url,
            'image_url': self.image_url,
            'user_id': self.user_id  # Добавим user_id в словарь
        }
        if include_attachments:
            data['attachments'] = [attachment.to_dict() for attachment in self.attachments]
        return data

class ListItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200))
    is_checked = db.Column(db.Boolean, default=False)
    note_id = db.Column(db.Integer, db.ForeignKey('note.id'))
    order = db.Column(db.Integer)

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'is_checked': self.is_checked,
            'order': self.order
        }

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    note_id = db.Column(db.Integer, db.ForeignKey('note.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'note_id': self.note_id,
            'created_at': self.created_at.isoformat()
        }

class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_url = db.Column(db.String(255), nullable=False)
    note_id = db.Column(db.Integer, db.ForeignKey('note.id'), nullable=False)
    note = db.relationship('Note', back_populates='attachments')

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'file_url': self.file_url
        }

class MonthInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    norm_hours = db.Column(db.Float)
    total_hours = db.Column(db.Float)
    night_hours = db.Column(db.Float)
    salary = db.Column(db.Float)
    advance = db.Column(db.Float)

    user = db.relationship('User', backref=db.backref('month_infos', lazy=True))
