from datetime import datetime
from gradedisplay import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True) #the long id number of the student for the db.
    schoolID = db.Column(db.Integer, nullable=False, unique=True) #the id number of the student.
    signupDate = db.Column(db.DateTime)
    assignments = db.relationship('Assignment', backref="student", lazy=True);

    def __repr__(self):
        return f"ID Number: '{self.schoolID}'"

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    dueDate = db.Column(db.DateTime, nullable=False)
    studentID = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    completed = db.Column(db.Boolean, nullable = False)

    def __repr__(self):
        return f"Assignment: '{self.name}' is due on '{self.dueDate}'. Completed: {self.completed} It is owned by Student {self.studentID}"