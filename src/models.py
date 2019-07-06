from flask.ext.sqlalchemy import SQLAlchemy
from hashlib import md5
import datetime

db = SQLAlchemy()

class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(20), default = 'admin')
    password = db.Column(db.String(32), default = md5('admin123').hexdigest())

    def get_id(self):
        return unicode(self.id)

    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_tablename(self):
        return 'admin'

    def __repr__(self):
        return '<Admin %r %r>' % (self.name, self.password)

class Student(db.Model):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(50), index = True)
    email = db.Column(db.String(60))
    password = db.Column(db.String(32), default = md5('0000').hexdigest())
    courses = db.relationship('Course', secondary = 'student_course')
    student_homeworks = db.relationship('Student_Homework', backref = 'student', lazy = 'dynamic')
    feedbacks = db.relationship('Feedback', backref = 'student', lazy = 'dynamic')

    def get_id(self):
        return unicode(self.id)

    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_tablename(self):
        return 'student'

    def __init__(self, id, password, name = "", email = ""):
        self.id = id
        self.name = name
        self.email = email
        self.password = md5(password).hexdigest()

    def __repr__(self):
        return '<Student %r %r %r %r>' % (self.id, self.name, self.email, self.password)

class Teacher(db.Model):
    __tablename__ = 'teacher'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(50), index = True)
    email = db.Column(db.String(60))
    password = db.Column(db.String(32), default = md5('1111').hexdigest())
    courses = db.relationship('Course', backref = 'teacher', lazy = 'dynamic')

    def get_id(self):
        return unicode(self.id)

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True

    def get_tablename(self):
        return 'teacher'

    def __init__(self, id, password, name = "", email = ""):
        self.id = id + 1000000000000000
        self.name = name
        self.email = email
        self.password = md5(password).hexdigest()

    def __repr__(self):
        return '<Teacher %r %r %r %r>' % (self.id, self.name, self.email, self.password)

class Course(db.Model):
    __tablename__ = 'course'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100), index = True)
    time = db.Column(db.String(100))
    location = db.Column(db.String(100))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))
    students = db.relationship('Student', secondary = 'student_course')
    resources = db.relationship('Resource', backref = 'course', lazy = 'dynamic')
    notices = db.relationship('Notice', backref = 'course', lazy = 'dynamic')
    homeworks = db.relationship('Homework', backref = 'course', lazy = 'dynamic')
    tas = db.relationship('Ta', backref = 'course', lazy  = 'dynamic')

    def __init__(self, name, teacher_id, time = "", location = ""):
        self.name = name
        self.time = time
        self.location = location
        self.teacher_id = teacher_id

    def __repr__(self):
        return '<Course %r %r %r %r %r>' % (self.id, self.name, self.time, self.location, self.teacher_id)

class Student_Course(db.Model):
    __tablename__ = 'student_course'
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), primary_key = True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), primary_key = True)

    def __init__(self, student_id, course_id):
        self.student_id = student_id
        self.course_id = course_id

    def __repr__(self):
        return '<Student_Course %r %r>' % (self.student_id, self.course_id)

class Resource(db.Model):
    __tablename__ = 'resource'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(120), index = True)
    url = db.Column(db.String(254))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))

    def __init__(self, name, url, course_id):
        self.name = name
        self.url = url
        self.course_id = course_id

    def __repr__(self):
        return '<Resource %r %r %r %r>' % (self.id, self.name, self.url, self.course_id)

class Notice(db.Model):
    __tablename__ = 'notice'
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(120))
    content = db.Column(db.Text)
    time = db.Column(db.DateTime, default = datetime.datetime.now)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))

    def __init__(self, title, content, course_id):
        self.title = title
        self.content = content
        self.course_id = course_id

    def __repr__(self):
        return '<Notice %r %r %r %r %r>' % (self.id, self.title, self.content, self.time, self.course_id)

class Homework(db.Model):
    __tablename__ = 'homework'
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(120))
    content = db.Column(db.Text)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    student_homeworks = db.relationship('Student_Homework', backref = 'homework', lazy = 'dynamic')
    feedbacks = db.relationship('Feedback', backref = 'homework', lazy = 'dynamic')

    def __init__(self, title, content, course_id):
        self.title = title
        self.content = content
        self.course_id = course_id

    def __repr__(self):
        return '<Homework %r %r %r %r>' % (self.id, self.title, self.content, self.course_id)

class Student_Homework(db.Model):
    __tablename__ = 'student_homework'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(120), index = True)
    time = db.Column(db.DateTime, default = datetime.datetime.now)
    url = db.Column(db.String(254))
    score = db.Column(db.Integer)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    homework_id = db.Column(db.Integer, db.ForeignKey('homework.id'))

    def __init__(self, name, url, student_id, homework_id, score = -1):
        self.name = name
        self.url = url
        self.score = score
        self.student_id = student_id
        self.homework_id = homework_id

    def __repr__(self):
        return '<Student_Homework %r %r %r %r %r %r %r>' % (self.id, self.name, self.time, self.url, self.score, self.student_id, self.homework_id)

class Feedback(db.Model):
    __tablename__ = 'feedbask'
    id = db.Column(db.Integer, primary_key = True)
    content = db.Column(db.Text)
    time = db.Column(db.DateTime, default = datetime.datetime.now)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    homework_id = db.Column(db.Integer, db.ForeignKey('homework.id'))

    def __init__(self, content, student_id, homework_id):
        self.content = content
        self.student_id = student_id
        self.homework_id = homework_id

    def __repr__(self):
        return '<Feedback %r %r %r %r %r>' % (self.id, self.content, self.time, self.student_id, self.homework_id)

class Ta(db.Model):
    __tablename__ = 'ta'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(50))
    password = db.Column(db.String(32), default = md5('2222').hexdigest())
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))

    def __init__(self, name, password, course_id):
        self.name = name
        self.password = md5(password).hexdigest()
        self.course_id = course_id

    def __repr__(self):
        return '<Ta %r %r %r %r>' % (self.id, self.name, self.password, self.course_id)