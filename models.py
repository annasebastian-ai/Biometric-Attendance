from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class Finger(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    registernumber = db.Column(db.String(100))
    gender = db.Column(db.String(10))
    email = db.Column(db.String(150), unique=True)
    template = db.Column(db.String(150))
    checkindate = db.Column(db.String(100))
    time_in = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    name = db.Column(db.String(150))
    


class UserLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    registernumber = db.Column(db.Float, nullable=False)
    checkindate = db.Column(db.Date, nullable=False)
    timein = db.Column(db.Time, nullable=False)
    finger_id = db.Column(db.Integer, db.ForeignKey('finger.id'))