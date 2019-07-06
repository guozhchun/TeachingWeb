#coding=utf-8
from flask import Flask, render_template, redirect, flash, session, url_for, request, g, abort, send_from_directory
from flask.ext.login import LoginManager, login_user, logout_user, current_user, login_required
from flask.ext.bootstrap import Bootstrap
from forms import LoginForm, AddStudentForm, AddCourseForm, NoticeForm, FileForm, EditForm, CourseForm, FeedbackForm, DeleteStudentForm, AddPersonForm, DeletePersonForm, ChangePasswordForm, SearchPageForm, CheckBoxForm
from models import db, Student, Admin, Teacher, Course, Student_Course, Resource, Notice, Homework, Student_Homework, Feedback
from sqlalchemy import and_
from werkzeug import secure_filename
from hashlib import md5
from functools import wraps
import sys, os, xlrd, datetime


reload(sys) 
sys.setdefaultencoding('utf-8')
basedir = os.getcwd()
#init
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']= 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SECRET_KEY'] = '12330098 teaching web'

db.app = app
db.init_app(app)
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'
bootstrap = Bootstrap(app)

DEFAULT = 1000000000000000  #：为了避免teacher表和student表拥有同一个id造成load_user错误，将这个默认值加在teacher表的id上
PAGE_ITEMS = 50    #：一个页面显示的记录数

@app.before_request
def before_request():
    g.user = current_user

def teacher_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.is_anonymous():
            abort(403)
        if not current_user.get_tablename() == 'teacher':
            abort(403)
        return f(*args, **kwargs)
    return decorated

def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.is_anonymous():
            abort(403)
        if not current_user.get_tablename() == 'student':
            abort(403)
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.is_anonymous():
            abort(403)
        if not current_user.get_tablename() == 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated

@lm.user_loader
def load_user(id):
    if Admin.query.get(int(id)) is None:
        if Teacher.query.get(int(id)) is None:
            return Student.query.get(int(id))
        else:
            return Teacher.query.get(int(id))
    else:
        return Admin.query.get(int(id))

@app.route('/', methods = ['GET', 'POST'])
@app.route('/login', methods = ['POST', 'GET'])
def login():
    if g.user is not None and g.user.is_authenticated:
        if g.user.get_tablename() == 'admin':
            return redirect(url_for('student_list'))
        elif g.user.get_tablename() == 'teacher':
            return redirect(url_for('teacher'))
        else:
            return redirect(url_for('student'))

    form = LoginForm()
    if form.validate_on_submit():
        usertype = form.usertype.data
        username = form.username.data
        password = form.password.data
        if usertype == 'admin':
            user = Admin.query.filter_by(name = username).first()
            if user is not None and user.password == md5(password).hexdigest():
                flash('login success!')
                login_user(user)
                return redirect(url_for('student_list'))
        elif usertype == 'teacher':
            user = None
            if username.isdigit():
                user = Teacher.query.filter_by(id = int(username) + DEFAULT).first()
            if user is not None and user.password == md5(password).hexdigest():
                flash('login success!')
                login_user(user)
                return redirect(url_for('teacher'))
        else:
            user = Student.query.filter_by(id = username).first()
            if user is not None and user.password == md5(password).hexdigest():
                flash('login success!')
                login_user(user)
                return redirect(url_for('student'))
        flash(u'用户名或密码错误，请重新登录！')
    return render_template('login.html', form = form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

#：教师登录后的主页
@app.route('/teacher')
@login_required
@teacher_required
def teacher():
    courses = db.session.query(Course).filter_by(teacher_id = g.user.id).all()
    return render_template('teacher.html', user = g.user, courses = courses)

#：修改个人信息的函数
@app.route('/profile', methods = ['GET', 'POST'])
@login_required
def profile():
    user = g.user
    form = EditForm()
    #：如果是管理员，则禁止访问
    if current_user.get_tablename() == 'admin':
        abort(403)
    if form.validate_on_submit():
        user.name = form.name.data
        user.email = form.email.data
        if form.password.data and form.password.data != "":
            user.password = md5(form.password.data).hexdigest()
        db.session.commit()
        flash(u'修改信息成功')
        return redirect(url_for('profile'))
    return render_template('profile.html', user = user, form = form)

#：获取教师所教课程的学生名单，传入参数id为课程id
@app.route('/teacher/course/<id>')
@login_required
def teacher_course(id):
    course = Course.query.get(id)
    students = course.students
    #：如果当前登录的教师没有教授这门课程，则禁止访问
    if current_user.id != course.teacher.id:
        abort(403)
    return render_template('teacherCourse.html', course = course, students = students)

#：判断文件类型是否是所要求的格式
def allow_file(filename, filetype):
    return '.' in filename and filename.rsplit('.', 1)[1] in filetype

#：保存文件到服务器上，并返回在服务器上的地址
def upload(file, filetype, addr = 'upload/'):
    address = None
    if file and allow_file(filename = file.filename, filetype = filetype):
        filename = secure_filename(file.filename)
        if not os.path.exists(addr):
            os.makedirs(addr)
        address = addr + filename
        while os.path.exists(address):
            address += '1'
        file.save(address)
    return address

#：为课程添加学生，传入参数id为课程id
@app.route('/teacher/addStudent/<id>', methods = ['GET', 'POST'])
@login_required
def add_student(id):
    course = Course.query.get(id)
    form = AddStudentForm()
    #：如果当前登录的教师没有教授这门课程，则禁止访问
    if current_user.id != course.teacher.id:
        abort(403)
    if form.validate_on_submit():
        addtype = form.addtype.data
        #: 如果是单个手动添加
        if addtype == 'single':
            student_id = form.student_id.data
            if student_id is None or student_id == "":
                flash(u'请填写学号')
                return render_template('addStudent.html', course = course, form = form)
            student = Student.query.get(student_id)
            if student is None:
                flash(u'学生不存在，请联系管理员添加学生')
                return render_template('addStudent.html', course = course, form = form)
            student_course = Student_Course.query.filter(and_(Student_Course.student_id == student_id, Student_Course.course_id == id)).first()
            if student_course is not None:
                flash(u'学生已经添加到课程中了，无需重复添加')
                return render_template('addStudent.html', course = course, form = form)
            sc = Student_Course(student_id = student_id, course_id = id)
            db.session.add(sc)
            db.session.commit()
            flash(u'成功增加学生到这门课程上')
            return redirect(url_for('teacher_course', id = id))
        #：上传文件批量添加，对于文件内能插入的学生直接插入，否则做错误处理显示错误信息
        else:
            notexistList = [] #：存放学生不存在Student表的数据
            existedList = []  #：存放学生已经添加到课程的数据
            isError = False
            isAdd = False
            address = upload(form.student_file.data, ['xls', 'xlsx']) #：将文件保存到服务器并返回文件地址
            if address is not None:
                #：使用xlrd模块读取excel文件
                data = xlrd.open_workbook(address) 
                table = data.sheets()[0]
                for i in range(table.nrows):
                    line = table.row_values(i)
                    #：防止数据不是数字，使用异常处理
                    try:
                        if type(eval(str(line[0]))) == float or str(line[0]).isdigit():
                            student_id = int(line[0])
                            student = Student.query.get(student_id)
                            if student is None:                     #：学生不在Student表中
                                notexistList.append(student_id)
                                isError = True
                                continue
                            student_course = Student_Course.query.filter(and_(Student_Course.student_id == student_id, Student_Course.course_id == id)).first()
                            if student_course is not None:          #：学生已经添加了这门课程
                                existedList.append(student_id)
                                isError = True
                                continue
                            isAdd = True
                            sc = Student_Course(student_id = student_id, course_id = id)
                            db.session.add(sc)
                    except:
                        continue #：对于不符合的数据，直接跳过不处理
                #：删除上传的文件
                if os.path.exists(address):
                    os.remove(address)
                #：对没有成功添加的数据进行处理，显示给客户
                if isError:
                    message = ""
                    if notexistList:
                        message = u'学生'
                        for error in notexistList:
                            message += '"' + str(error) + '" '
                        message += u'不存在，请联系管理员添加学生。'
                        flash(message)
                    if existedList:
                        message = u'学生'
                        for error in existedList:
                            message += '"' + str(error) + '" '
                        message += u'已经添加到课程中了，无需重复添加'
                        flash(message)
                    db.session.commit()
                    return render_template('addStudent.html', course = course, form = form)
                elif isAdd:
                    db.session.commit()
                    flash(u'所有学生成功添加到课程')
                    return redirect(url_for('teacher_course', id = id))
                else:
                    flash(u'请选择正确的文件格式上传文件')
                    return render_template('addStudent.html', course = course, form = form)
            else:
                flash(u'请选择正确的文件格式上传文件')
                return render_template('addStudent.html', course = course, form = form)
    return render_template('addStudent.html', course = course, form = form)

#：删除课程学生的函数，传入参数id为课程id
@app.route('/teacher/deleteStudent/<id>', methods = ['GET', 'POST'])
@login_required
def delete_student(id):
    course = Course.query.get(id)
    form = DeleteStudentForm()
    #：如果当前登录的教师没有教授这门课程，则禁止访问
    if current_user.id != course.teacher.id:
        abort(403)
    if form.validate_on_submit():
        deletetype = form.deletetype.data
        #：单个手动删除
        if deletetype == 'single':
            student_id = form.student_id.data
            if student_id is None or student_id == "":
                flash(u'请填写学号')
                return render_template('deleteStudent.html', form = form, course = course)
            student = Student.query.get(student_id)
            if student is None:
                flash(u'学生不存在，不能删除')
                return render_template('deleteStudent.html', form = form, course = course)
            student_course = Student_Course.query.filter(and_(Student_Course.student_id == student_id, Student_Course.course_id == id)).first()
            if student_course is None:
                flash(u'学生没有选这门课，不能删除')
                return render_template('deleteStudent.html', form = form, course = course)
            #：删除该学生该课程的所有作业，包括文件和记录
            student_homeworks = student.student_homeworks.all()
            for student_homework in student_homeworks:
                if student_homework.homework.course_id == int(id):
                    if os.path.exists(student_homework.url):
                        os.remove(student_homework.url)
                    db.session.delete(student_homework)
            #：删除该学生该课程的反馈
            feedbacks = student.feedbacks.all()
            for feedback in feedbacks:
                if feedback.homework.course_id == int(id):
                    db.session.delete(feedback)
            db.session.delete(student_course)   #：删除学生选这门课的记录
            db.session.commit()
            flash(u'删除学生成功')
            return redirect(url_for('teacher_course', id = id))
        #：文件批量删除
        else:
            errorList = []     #：存放不能删除的学生学号
            isError = False    #：是否有不能删除的学生
            isDelete = False   #：是否有成功删除的学生
            address = upload(form.student_file.data, ['xls', 'xlsx']) #：将文件保存到服务器并返回文件地址
            if address is None:
                flash(u'请选择正确的文件格式上传文件')
                return render_template('deleteStudent.html', form = form, course = course)
            #：使用xlrd模块读取excel文件
            data = xlrd.open_workbook(address) 
            table = data.sheets()[0]
            for i in range(table.nrows):
                line = table.row_values(i)
                #：为了防止数据不是数字，使用异常处理
                try:
                    if type(eval(str(line[0]))) == float or str(line[0]).isdigit():
                        student_id = int(line[0])
                        student = Student.query.get(student_id)
                        if student is None:                      #：学生不存在
                            isError = True
                            errorList.append(student_id)
                            continue
                        student_course = Student_Course.query.filter(and_(Student_Course.student_id == student_id, Student_Course.course_id == id)).first()
                        if student_course is None:               #：学生没有选这门课
                            isError = True
                            errorList.append(student_id)
                            continue
                        isDelete = True
                        #：删除该学生该课程的所有作业，包括文件和记录
                        student_homeworks = student.student_homeworks.all()
                        for student_homework in student_homeworks:
                            if student_homework.homework.course_id == int(id):
                                if os.path.exists(student_homework.url):
                                    os.remove(student_homework.url)
                                db.session.delete(student_homework)
                        #：删除该学生该课程的反馈
                        feedbacks = student.feedbacks.all()
                        for feedback in feedbacks:
                            if feedback.homework.course_id == int(id):
                                db.session.delete(feedback)
                        db.session.delete(student_course)   #：删除学生选这门课的记录
                except:
                    continue     #：对于不符合的数据，直接跳过不处理
            #：删除上传的文件
            if os.path.exists(address):
                os.remove(address)
            #：处理批量删除的错误就结果
            if isError:
                message = u'学生'
                for error in errorList:
                    message += '"' + str(error) + '" '
                message += u'没有选这门课，不能删除'
                flash(message)
                db.session.commit()
                return render_template('deleteStudent.html', form = form, course = course)
            elif isDelete:
                flash(u'所有学生成功从此课程中删除')
                db.session.commit()
                return redirect(url_for('teacher_course', id = id))
            else:
                flash(u'请选择正确的文件格式上传文件')
                return render_template('deleteStudent.html', form = form, course = course)
    return render_template('deleteStudent.html', form = form, course = course)

#：教师增加课程的函数
@app.route('/teacher/addCourse', methods = ['POST', 'GET'])
@login_required
@teacher_required
def add_course():
    teacher = current_user
    form = AddCourseForm()
    if form.validate_on_submit():
        course = Course(teacher_id = teacher.id, name = form.course_name.data, time = form.time.data, location = form.location.data)
        db.session.add(course)
        db.session.commit()
        flash(u'你已经成功添加课程 < ' + form.course_name.data + ' >' + u'。现在为该课程添加学生吧')
        return redirect(url_for('add_student', id = course.id))
    return render_template('addCourse.html', form = form, user = teacher)

#：根据课程删除与课程相关的信息的函数
def delete_course_by_course(course):
    #：删除该课程的所有公告
    notices = course.notices.all()
    for notice in notices:
        db.session.delete(notice)
    #：删除该课程的所有课件
    resources = course.resources.all()
    for resource in resources:
        if os.path.exists(resource.url):
            os.remove(resource.url)
        db.session.delete(resource)
    #：删除该课程的所有作业和与作业有关的内容，包括反馈、文件等
    homeworks = course.homeworks.all()
    for homework in homeworks:
        #：删除学生上传的作业的文件和记录
        student_homeworks = homework.student_homeworks.all()
        for student_homework in student_homeworks:
            #：从服务器上删除学生上传的文件
            if os.path.exists(student_homework.url):
                os.remove(student_homework.url)
            #：删除Student_Homework表中的记录
            db.session.delete(student_homework)
        #：删除反馈
        feedbacks = homework.feedbacks
        for feedback in feedbacks:
            db.session.delete(feedback)
        #：删除本条作业记录
        db.session.delete(homework)
    #：删除学生选修这门课程记录
    student_courses = Student_Course.query.filter_by(course_id = course.id).all()
    for student_course in student_courses:
        db.session.delete(student_course)
    #：删除本课程的记录
    db.session.delete(course)

#：删除课程的函数，传入参数id为课程id
@app.route('/teacher/deleteCourse/<id>')
@login_required
def delete_course(id):
    course = Course.query.get(id)
    #：如果当前登录的教师没有教授这门课程，则禁止访问
    if current_user.id != course.teacher_id:
        abort(403)
    delete_course_by_course(course)
    db.session.commit()
    flash(u'成功删除课程')
    return redirect(url_for('teacher'))

#：显示修改课程信息的函数，传入id为课程id
@app.route('/teacher/course/details/<id>', methods = ['GET', 'POST'])
@login_required
def course_details(id):
    course = Course.query.get(id)
    form = CourseForm()
    #：如果当前登录的教师没有教授这门课程，则禁止访问
    if current_user.id != course.teacher.id:
        abort(403)
    if form.validate_on_submit():
        course.time = form.time.data
        course.location = form.location.data
        flash(u'修改信息成功')
        db.session.commit()
        return redirect(url_for('course_details', id = id))
    return render_template('courseDetails.html', form = form, course = course)

#：发布公告的函数，传入参数id为课程id
@app.route('/teacher/notice/<id>', methods = ['POST', 'GET'])
@login_required
def notice(id):
    course = Course.query.get(id)
    notices = course.notices.order_by(Notice.id.desc()).all()  #：获取课程公告，按时间从近到远
    form = NoticeForm()
    #：如果当前登录的教师没有教授这门课程，则禁止访问
    if current_user.id != course.teacher.id:
        abort(403)
    if form.validate_on_submit():
        notice = Notice(title = form.title.data, content = form.content.data, course_id = id)
        db.session.add(notice)
        db.session.commit()
        flash(u'发布公告成功！')
        return redirect(url_for('notice', id = id))
    return render_template('teacherNotice.html', form = form, course = course, notices = notices)

#：删除公告的函数，输入参数id为该公告的id
@app.route('/teacher/delete_notice/<id>')
@login_required
def delete_notice(id):
    notice = Notice.query.get(id)
    #：如果该公告的发布者不是当前登录的教师，则禁止访问
    if current_user.id != notice.course.teacher.id:
        abort(403)
    db.session.delete(notice)
    db.session.commit()
    flash(u'公告已删除！')
    return redirect(url_for('notice', id = notice.course_id))

#：教师上传显示课件的函数，传入参数id为课程id
@app.route('/teacher/resource/<id>', methods = ['GET', 'POST'])
@login_required
def teacher_resource(id):
    course = Course.query.get(id)
    resources = course.resources.all()
    form = FileForm()
    #：如果当前登录的教师没有教授这门课程，则禁止访问
    if current_user.id != course.teacher.id:
        abort(403)
    if form.validate_on_submit():
        name = form.file.data.filename
        addr = 'upload/' + str(id) + '/' + 'resource/' 
        url = upload(form.file.data, ['zip', 'rar', 'doc', 'txt', 'docx', 'pdf', 'ppt', 'pptx'], addr)
        if url is None:
            flash(u'请选择正确的文件格式上传文件，文件格式可以是["zip", "rar", "doc", "txt", "docx", "pdf", "ppt", "pptx"]')
            return render_template('teacherResource.html', form = form, course = course, resources = resources)
        resource = Resource.query.filter(and_(Resource.course_id == id, Resource.name == name)).first()
        #：如果是同名文件，则覆盖，即删除原文件，保留新文件
        if resource is not None:
            #：删除原文件
            if os.path.exists(resource.url):
                os.remove(resource.url)
            resource.url = url
            db.session.commit()
        else:
            resource = Resource(name = name, url = url, course_id = id)
            db.session.add(resource)
            db.session.commit()
        flash(u'文件上传成功')
        return redirect(url_for('teacher_resource', id = id))
    return render_template('teacherResource.html', form = form, course = course, resources = resources)

#：分解URL地址的函数，返回最后‘/’前面的内容和后面的内容
def splitUrl(url):
    tmp = url.split('/')
    filename = tmp[-1]
    addr = ""
    for i in range(len(tmp) - 1):
        addr += tmp[i] + '/'
    return addr, filename

#：课件下载的函数，输入参数id为课件id，name为课件名字
#：虽然函数中只用到了id，但是为了让下载的文件名字和上传的一致，route中使用<name>放在<id>后
@app.route('/download/resource/<id>/<name>')
@login_required
def download_resource(id, name):
    resource = Resource.query.get(id)
    addr, filename = splitUrl(resource.url)
    #：如果当前登录的用户不是上传该课件的教师，也不是该课件所属课程的学生，则禁止访问
    if current_user.id != resource.course.teacher.id and current_user not in resource.course.students:
        abort(403)
    return send_from_directory(addr, filename)

#：删除课件的函数，传入参数id为课件id
@app.route('/teacher/delete_resource/<id>')
@login_required
def delete_resource(id):
    resource = Resource.query.get(id)
    #：如果该资源属于的课程的开课老师不是当前登录的教师，则禁止访问
    if current_user.id != resource.course.teacher.id:
        abort(403)
    if os.path.exists(resource.url):
        os.remove(resource.url)         #：从服务器上删除文件
    db.session.delete(resource)
    db.session.commit()
    flash(u'课件已删除！')
    return redirect(url_for('teacher_resource', id = resource.course_id))

#：教师发布作业和显示作业的函数，传入参数id为课程id
@app.route('/teacher/homework/<id>', methods = ['POST', 'GET'])
@login_required
def homework(id):
    course = Course.query.get(id)
    homeworks = course.homeworks.all()
    form = NoticeForm()
    #：如果当前登录的教师没有教授这门课程，则禁止访问
    if current_user.id != course.teacher.id:
        abort(403)
    if form.validate_on_submit():
        homework = Homework(title = form.title.data, content = form.content.data, course_id = id)
        db.session.add(homework)
        db.session.commit()
        flash(u'发布作业成功！')
        return redirect(url_for('homework', id = id))
    return render_template('teacherHomework.html', form = form, course = course, homeworks = homeworks)

#：教师删除作业的函数，传入参数id为作业id
@app.route('/teacher/delete_homework/<id>')
@login_required
def delete_homework(id):
    homework = Homework.query.get(id)
    student_homeworks = homework.student_homeworks.all()
    feedbacks = homework.feedbacks.all()
    #：如果当前登录用户不是发布该作业的教师，则禁止访问
    if current_user.id != homework.course.teacher.id:
        abort(403)
    #：删除该作业下学生上传的作业
    for student_homework in student_homeworks:
        #：从服务器上删除学生上传的文件
        if os.path.exists(student_homework.url):
            os.remove(student_homework.url)
        #：删除Student_Homework表中的记录
        db.session.delete(student_homework)
    #：删除该作业下学生的反馈
    for feedback in feedbacks:
        db.session.delete(feedback)
    db.session.delete(homework)  #：删除作业本条记录
    db.session.commit()
    flash(u'删除作业成功')
    return redirect(url_for('homework', id = homework.course_id))

#：此函数用于教师显示作业详情，传入参数id为作业id
@app.route('/teacher/homework/details/<id>')
@login_required
def teacher_homework_details(id):
    homework = Homework.query.get(id)
    student_homeworks = homework.student_homeworks.order_by(Student_Homework.student_id).all()
    feedbacks = homework.feedbacks.all()
    #：如果当前作业所属课程的老师不是当前登录教师，则禁止访问
    if current_user.id != homework.course.teacher.id:
        abort(403)
    return render_template('teacherHomeworkDetails.html', course = homework.course, student_homeworks = student_homeworks, feedbacks = feedbacks, homework = homework)

#：学生登录的主页
@app.route('/student')
@login_required
@student_required
def student():
    courses = g.user.courses
    return render_template('student.html', user = g.user, courses = courses)

#：学生某个课程的主页，获取该主页的公告内容，传入参数id为课程id
@app.route('/student/course/<id>')
@login_required
@student_required
def student_course(id):
    course = Course.query.get(id)
    notices = course.notices.order_by(Notice.id.desc()).all()  #：获取课程公告，按时间从近到远
    #：如果该公告所属课程的学生中不包含当前登录的学生，则禁止访问
    if current_user not in course.students:
        abort(403)
    return render_template('studentCourse.html', course = course, notices = notices)

#：学生显示课程课件的函数，传入参数id为课程id
@app.route('/student/resource/<id>')
@login_required
def student_resource(id):
    course = Course.query.get(id)
    resources = course.resources.all()
    #：如果该课件所属课程的学生中不包含当前登录的学生，则禁止访问
    if current_user not in course.students:
        abort(403)
    return render_template('studentResource.html', course = course, resources = resources)

#：显示学生课程作业的函数，传入参数id为课程id
@app.route('/student/homework/<id>')
@login_required
def student_homework(id):
    course = Course.query.get(id)
    homeworks = course.homeworks.all()
    #：如果该作业所属课程的学生中不包含当前登录的学生，则禁止访问
    if current_user not in course.students:
        abort(403)
    return render_template('studentHomework.html', course = course, homeworks = homeworks)

#：显示学生课程作业详细信息的函数，传入参数id为作业id
@app.route('/student/homework/details/<id>', methods = ['GET', 'POST'])
@login_required
def student_homework_details(id):
    homework = Homework.query.get(id)
    student_homework = Student_Homework.query.filter(and_(Student_Homework.student_id == current_user.id, Student_Homework.homework_id == id)).first()
    feedbacks = homework.feedbacks.all()
    form = FileForm()
    feedbackForm = FeedbackForm()
    #: 如果当前学生没有选择该课程，但是要访问该课程的作业内容，则禁止访问
    if current_user not in homework.course.students:
        abort(403)
    #：上传文件
    if form.validate_on_submit():
        name = form.file.data.filename
        addr = 'upload/' + str(homework.course_id) + '/homework/' + str(id) + '/' + str(current_user.id) + '/'
        url = upload(form.file.data, ['zip', 'rar', 'doc', 'txt', 'docx', 'pdf', 'ppt', 'pptx'], addr)
        if url is None:
            flash(u'请选择正确的文件格式上传文件，文件格式可以是["zip", "rar", "doc", "txt", "docx", "pdf", "ppt", "pptx"]')
            return render_template('studentHomeworkDetails.html', homework = homework, form = form, course = homework.course, student_homework = student_homework, feedbacks = feedbacks, feedbackForm = feedbackForm)
        #：如果重复上传，则覆盖原先的文件，即删除原先的文件，保留现有的文件
        if student_homework is not None:
            if student_homework.url != url and os.path.exists(student_homework.url):
                os.remove(student_homework.url)
            student_homework.name = name
            student_homework.url = url
            student_homework.time = datetime.datetime.now()
            db.session.commit()
        else:
            student_homework = Student_Homework(name = name, url = url, homework_id = id, student_id = current_user.id)
            db.session.add(student_homework)
            db.session.commit()
        flash(u'文件上传成功')
        return redirect(url_for('student_homework_details', id = id))
    #：发布反馈内容
    if feedbackForm.validate_on_submit():
        content = feedbackForm.content.data
        feedback = Feedback(content = content, student_id = current_user.id, homework_id = id)
        db.session.add(feedback)
        db.session.commit()
        flash(u'反馈内容成功发表')
        return redirect(url_for('student_homework_details', id = id))
    return render_template('studentHomeworkDetails.html', homework = homework, form = form, course = homework.course, student_homework = student_homework, feedbacks = feedbacks, feedbackForm = feedbackForm)

#：作业下载的函数，输入参数id为Student_Homework.id，name为Student_Homework.name
#：虽然函数中只用到了id，但是为了让下载的文件名字和上传的一致，route中使用<name>放在<id>后
@app.route('/download/homework/<id>/<name>')
@login_required
def download_homework(id, name):
    student_homework = Student_Homework.query.get(id)
    addr, filename = splitUrl(student_homework.url)
    #：如果当前登录用户不是该作业的上传者，也不是该作业所属课程的老师，则禁止访问
    if current_user.id != student_homework.student_id and current_user.id != student_homework.homework.course.teacher.id:
        abort(403)
    return send_from_directory(addr, filename)

#：为管理员添加学生和教师的上传文件提供样本下载
@app.route('/download/sample/<name>')
@login_required
@admin_required
def download_sample(name):
    return send_from_directory('upload/sample', name)

#：管理员登录的主页，也是显示学生名单的信息的页面
@app.route('/admin', methods = ['GET', 'POST'])
@app.route('/admin/<int:page>', methods = ['GET', 'POST'])
@login_required
@admin_required
def student_list(page = 1):
    form = SearchPageForm()
    checkBoxForm = CheckBoxForm()
    students = Student.query.paginate(page, PAGE_ITEMS, False)
    #：页面跳转表单
    if form.validate_on_submit():
        if form.page.data <= students.pages and form.page.data > 0:
            return redirect(url_for('student_list', page = form.page.data))
    #：复选框的表单，用于删除
    if checkBoxForm.validate_on_submit():
        checkBoxList = request.form.getlist("checkItem")     #：获取选中的学生
        #：删除选中的学生及其相关的东西
        for item in checkBoxList:
            student = Student.query.get(int(item))
            delete_student_by_student(student)    #：删除学生以及与这个学生相关的东西
        db.session.commit()
        flash(u'学生删除成功')
        return redirect(url_for('student_list'))
    return render_template('studentList.html', students = students, form = form, checkBoxForm = checkBoxForm)

#：管理员显示教师名单信息的页面
@app.route('/admin/teacherList', methods = ['POST', 'GET'])
@app.route('/admin/teacherList/<int:page>', methods = ['POST', 'GET'])
@login_required
@admin_required
def teacher_list(page = 1):
    form = SearchPageForm()
    checkBoxForm = CheckBoxForm()
    teachers = Teacher.query.paginate(page, PAGE_ITEMS, False)
    #：页面跳转表单
    if form.validate_on_submit():
        if form.page.data <= teachers.pages and form.page.data > 0:
            return redirect(url_for('teacher_list', page = form.page.data))
    #：复选框的表单，用于删除
    if checkBoxForm.validate_on_submit():
        checkBoxList = request.form.getlist("checkItem")
        #：删除选中的教师及其相关内容
        for item in checkBoxList:
            teacher = Teacher.query.get(int(item))
            delete_teacher_by_teacher(teacher)     #：删除教师及其相关内容
        db.session.commit()
        flash(u'教师删除成功')
        return redirect(url_for('teacher_list'))
    return render_template('teacherList.html', teachers = teachers, form = form, checkBoxForm = checkBoxForm)

#：管理员增加学生到学生表的函数
@app.route('/admin/addStudent', methods = ['POST', 'GET'])
@login_required
@admin_required
def admin_add_student():
    form = AddPersonForm()
    if form.validate_on_submit():
        if form.addtype.data == 'single':
            id = form.id.data
            name = form.name.data
            email = form.email.data
            password = form.password.data
            if id is None or id == "":
                flash(u'学号不能为空')
                return render_template('adminAddStudent.html', form = form)
            if not id.isdigit():
                flash(u'学号必须为整数')
                return render_template('adminAddStudent.html', form = form)
            student = Student.query.get(id)
            if student is not None:
                flash(u'学生已经存在，不能重复添加')
                return render_template('adminAddStudent.html', form = form)
            if password is None or password == "":     #：如果密码为空，则默认密码为学号
                password = str(id)
            student = Student(id = id, name = name, email = email, password = password)
            db.session.add(student)
            db.session.commit()
            flash(u'添加学生成功')
            return redirect(url_for('student_list'))
        else:
            errorList = []
            isError = False
            isAdd = False
            address = upload(form.file.data, ['xls', 'xlsx']) #：将文件保存到服务器并返回文件地址
            if address is None:
                flash(u'请选择正确的文件格式上传文件')
                return render_template('adminAddStudent.html', form = form)
            #：使用xlrd模块读取excel文件
            data = xlrd.open_workbook(address) 
            table = data.sheets()[0]
            for i in range(table.nrows):
                line = table.row_values(i)
                try:
                    if type(eval(str(line[0]))) == float or str(line[0]).isdigit():
                        id = int(line[0])
                        student = Student.query.get(id)
                        if student is not None:
                            isError = True
                            errorList.append(id)
                            continue
                        isAdd = True
                        name = line[1]
                        email = str(line[2])
                        password = str(line[3])
                        if password is None or password == "":
                            password = str(id)
                        student = Student(id = id, name = name, email = email, password = password)
                        db.session.add(student)
                except:
                    continue   #：对不符合的数据不做处理，直接跳过
            #：删除上传的文件
            if os.path.exists(address):
                os.remove(address)
            #：对错误结果进行处理
            if isError:
                message = u'学生'
                for error in errorList:
                    message += '"' + str(error) + '" '
                message += u'已经存在，不能重复添加'
                flash(message)
                db.session.commit()
                return render_template('adminAddStudent.html', form = form)
            elif isAdd:
                db.session.commit()
                flash(u'全部学生添加成功')
                return redirect(url_for('student_list'))
            else:
                flash(u'请选择正确的文件格式上传文件')
                return render_template('adminAddStudent.html', form = form)
    return render_template('adminAddStudent.html', form = form)

#：管理员增加教师到教师表的函数
@app.route('/admin/addTeacher', methods = ['POST', 'GET'])
@login_required
@admin_required
def admin_add_teacher():
    form = AddPersonForm()
    if form.validate_on_submit():
        if form.addtype.data == 'single':
            id = form.id.data
            name = form.name.data
            email = form.email.data
            password = form.password.data
            if id is None or id == "":
                flash(u'工号不能为空')
                return render_template('adminAddTeacher.html', form = form)
            if not id.isdigit():
                flash(u'工号必须为整数')
                return render_template('adminAddTeacher.html', form = form)
            teacher = Teacher.query.get(int(id) + DEFAULT)
            if teacher is not None:
                flash(u'教师已经存在，不能重复添加')
                return render_template('adminAddTeacher.html', form = form)
            if password is None or password == "":     #：如果密码为空，则默认密码为工号
                password = str(id)
            teacher = Teacher(id = int(id), name = name, email = email, password = password)
            db.session.add(teacher)
            db.session.commit()
            flash(u'添加教师成功')
            return redirect(url_for('teacher_list'))
        else:
            errorList = []
            isError = False
            isAdd = False
            address = upload(form.file.data, ['xls', 'xlsx']) #：将文件保存到服务器并返回文件地址
            if address is None:
                flash(u'请选择正确的文件格式上传文件')
                return render_template('adminAddTeacher.html', form = form)
            #：使用xlrd模块读取excel文件
            data = xlrd.open_workbook(address) 
            table = data.sheets()[0]
            for i in range(table.nrows):
                line = table.row_values(i)
                try:
                    if type(eval(str(line[0]))) == float or str(line[0]).isdigit():
                        id = int(line[0])
                        teacher = Teacher.query.get(int(id) + DEFAULT)
                        if teacher is not None:
                            isError = True
                            errorList.append(id)
                            continue
                        isAdd = True
                        name = line[1]
                        email = str(line[2])
                        password = str(line[3])
                        if password is None or password == "":
                            password = str(id)
                        teacher = Teacher(id = int(id), name = name, email = email, password = password)
                        db.session.add(teacher)
                except:
                    continue   #：对不符合的数据不做处理，直接跳过
            #：删除上传的文件
            if os.path.exists(address):
                os.remove(address)
            #：对错误结果进行处理
            if isError:
                message = u'教师'
                for error in errorList:
                    message += '"' + str(error) + '" '
                message += u'已经存在，不能重复添加'
                flash(message)
                db.session.commit()
                return render_template('adminAddTeacher.html', form = form)
            elif isAdd:
                db.session.commit()
                flash(u'全部教师添加成功')
                return redirect(url_for('teacher_list'))
            else:
                flash(u'请选择正确的文件格式上传文件')
                return render_template('adminAddTeacher.html', form = form)
    return render_template('adminAddTeacher.html', form = form)

#：根据学生删除与学生相关的记录
def delete_student_by_student(student):
    #：删除与此学生有关的选课记录
    student_courses = Student_Course.query.filter_by(student_id = student.id).all()
    for student_course in student_courses:
        db.session.delete(student_course)
    #：删除此学生上传的作业与记录
    student_homeworks = student.student_homeworks.all()
    for student_homework in student_homeworks:
        if os.path.exists(student_homework.url):
            os.remove(student_homework.url)
        db.session.delete(student_homework)
    #：删除此学生的反馈
    feedbacks = student.feedbacks.all()
    for feedback in feedbacks:
        db.session.delete(feedback)
    #：删除此学生
    db.session.delete(student)

#：管理员删除学生的函数
@app.route('/admin/deleteStudent', methods = ['POST', 'GET'])
@login_required
@admin_required
def admin_delete_student():
    form = DeletePersonForm()
    if form.validate_on_submit():
        if form.deletetype.data == 'single':
            id = form.id.data
            if id is None or id == "":
                flash(u'学号不能为空')
                return render_template('adminDeleteStudent.html', form = form)
            student = Student.query.get(id)
            if student is None:
                flash(u'学生不存在，不能删除')
                return render_template('adminDeleteStudent.html', form = form)
            delete_student_by_student(student)  #：删除与此学生相关的记录
            db.session.commit()
            flash(u'删除学生成功')
            return redirect(url_for('student_list'))
        else:
            errorList = []
            isError = False
            isDelete = False
            address = upload(form.file.data, ['xls', 'xlsx']) #：将文件保存到服务器并返回文件地址
            if address is None:
                flash(u'请选择正确的文件格式上传文件')
                return render_template('adminDeleteStudent.html', form = form)
            #：使用xlrd模块读取excel文件
            data = xlrd.open_workbook(address) 
            table = data.sheets()[0]
            for i in range(table.nrows):
                line = table.row_values(i)
                try:
                    if type(eval(str(line[0]))) == float or str(line[0]).isdigit():
                        id = int(line[0])
                        student = Student.query.get(id)
                        if student is None:
                            errorList.append(id)
                            isError = True
                            continue
                        isDelete = True
                        delete_student_by_student(student)  #：删除与此学生相关的记录
                except:
                    continue
            #：删除上传的文件
            if os.path.exists(address):
                os.remove(address)
            #：处理错误信息
            if isError:
                message = u'学生'
                for error in errorList:
                    message += '"' + str(error) + '" '
                message += u'不存在，不能删除'
                flash(message)
                db.session.commit()
                return render_template('adminDeleteStudent.html', form = form)
            elif isDelete:
                db.session.commit()
                flash(u'所有学生全部删除成功')
                return redirect(url_for('student_list'))
            else:
                flash(u'请选择正确的文件格式上传文件')
                return render_template('adminDeleteStudent.html', form = form)
    return render_template('adminDeleteStudent.html', form = form)

#：根据教师删除与教师相关的记录和文件的函数
def delete_teacher_by_teacher(teacher):
    courses = teacher.courses.all()      #：获取教师教授的所有课程
    #：删除这些课程和与这些课程相关的东西
    for course in courses:
        delete_course_by_course(course)
    #：删除本条教师记录
    db.session.delete(teacher)

#：管理员删除教师的函数
@app.route('/admin/deleteTeacher', methods = ['POST', 'GET'])
@login_required
@admin_required
def admin_delete_teacher():
    form = DeletePersonForm()
    if form.validate_on_submit():
        if form.deletetype.data == 'single':
            id = form.id.data
            if id is None or id == "":
                flash(u'工号不能为空')
                return render_template('adminDeleteTeacher.html', form = form)
            teacher = None
            if id.isdigit():
                teacher = Teacher.query.get(int(id) + DEFAULT)
            if teacher is None:
                flash(u'教师不存在，不能删除')
                return render_template('adminDeleteTeacher.html', form = form)
            delete_teacher_by_teacher(teacher)  #：删除与此教师相关的记录
            db.session.commit()
            flash(u'删除教师成功')
            return redirect(url_for('teacher_list'))
        else:
            errorList = []
            isError = False
            isDelete = False
            address = upload(form.file.data, ['xls', 'xlsx']) #：将文件保存到服务器并返回文件地址
            if address is None:
                flash(u'请选择正确的文件格式上传文件')
                return render_template('adminDeleteTeacher.html', form = form)
            #：使用xlrd模块读取excel文件
            data = xlrd.open_workbook(address) 
            table = data.sheets()[0]
            for i in range(table.nrows):
                line = table.row_values(i)
                try:
                    if type(eval(str(line[0]))) == float or str(line[0]).isdigit():
                        id = int(line[0])
                        teacher = Teacher.query.get(int(id) + DEFAULT)
                        if teacher is None:
                            errorList.append(id)
                            isError = True
                            continue
                        isDelete = True
                        delete_teacher_by_teacher(teacher)  #：删除与此教师相关的记录
                except:
                    continue
            #：删除上传的文件
            if os.path.exists(address):
                os.remove(address)
            #：处理错误信息
            if isError:
                message = u'教师'
                for error in errorList:
                    message += '"' + str(error) + '" '
                message += u'不存在，不能删除'
                flash(message)
                db.session.commit()
                return render_template('adminDeleteTeacher.html', form = form)
            elif isDelete:
                db.session.commit()
                flash(u'所有教师全部删除成功')
                return redirect(url_for('teacher_list'))
            else:
                flash(u'请选择正确的文件格式上传文件')
                return render_template('adminDeleteTeacher.html', form = form)
    return render_template('adminDeleteTeacher.html', form = form)

#：管理员修改密码的函数
@app.route('/admin/changePassword', methods = ['POST', 'GET'])
@login_required
@admin_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if form.selecttype.data == 'admin':
            admin = Admin.query.filter_by(name = form.name.data).first()
            if admin is None:
                flash(u'用户不存在')
                return render_template('changePassword.html', form = form)
            admin.password = md5(form.password.data).hexdigest()
        elif form.selecttype.data == 'teacher':
            teacher = None
            if form.name.data.isdigit():
                teacher = Teacher.query.filter_by(id = int(form.name.data) + DEFAULT).first()
            if teacher is None:
                flash(u'用户不存在')
                return render_template('changePassword.html', form = form)
            teacher.password = md5(form.password.data).hexdigest()
        else:
            student = None
            if form.name.data.isdigit():
                student = Student.query.filter_by(id = int(form.name.data)).first()
            if student is None:
                flash(u'用户不存在')
                return render_template('changePassword.html', form = form)
            student.password = md5(form.password.data).hexdigest()
        db.session.commit()
        flash(u'修改密码成功')
        return redirect(url_for('change_password'))
    return render_template('changePassword.html', form = form)

if __name__ == '__main__':
    app.run(debug = True)