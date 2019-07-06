#coding=utf-8
from teachingWeb import db
from models import Admin, Student, Teacher, Course

db.create_all()

admin = Admin(name = 'admin', id = -1)
db.session.add(admin)
db.session.commit()

student = Student(id = 121, password = '121')
db.session.add(student)
db.session.commit()

teacher = Teacher(id = 1, password = '1')
db.session.add(teacher)
db.session.commit()

course = Course(name = 'DB', teacher_id = 1)
db.session.add(course)
db.session.commit()