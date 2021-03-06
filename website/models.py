from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

# database table for User
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    patients = db.relationship('Patient')

# database table for Patient
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(150))
    results = db.relationship('Result')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# database table for Result
class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.String(10000))
    percentage = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

