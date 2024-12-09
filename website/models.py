from . import db 
from flask_login import UserMixin
from sqlalchemy.sql import func


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    notes = db.relationship('Note')

class Attendance(db.Model):
    _id = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.String(5), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    date = db.Column(db.String(12), nullable=False)
    check1 = db.Column(db.String(10))
    check2 = db.Column(db.String(10))
    check3 = db.Column(db.String(10))
    check4 = db.Column(db.String(10))
    check5 = db.Column(db.String(10))
    check6 = db.Column(db.String(10))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())


