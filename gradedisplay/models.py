from datetime import datetime
from gradedisplay import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True) #the long id number of the student for the db.
    schoolID = db.Column(db.Integer, nullable=False, unique=True) #the id number of the student.
    signupDate = db.Column(db.DateTime)
    sortingMethod = db.Column(db.String(1), nullable=True)
    assignments = db.relationship('Assignment', backref="student", lazy=True)
    classes = db.relationship('Period', backref='period', lazy=True)

    def __repr__(self):
        return f"ID Number: '{self.schoolID}'"

class Period(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    teacher = db.Column(db.String(10), nullable=False)
    
    userDBI = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assignments = db.relationship('Assignment', backref='period', lazy=True)

    def __repr__(self):
        return f"{self.name} : {self.teacher}"

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    dueDate = db.Column(db.DateTime, nullable=False)
    completed = db.Column(db.Boolean, nullable = False)
    missing = db.Column(db.Boolean, nullable = False)

    userDBI = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    periodDBI = db.Column(db.Integer, db.ForeignKey('period.id'), nullable = True)

    def __repr__(self):
        return f"Name: '{self.name}' due '{self.dueDate}'. {self.period} Done: {self.completed} Student: {self.userDBI}"
