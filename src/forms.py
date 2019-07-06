#coding=utf-8
from flask.ext.wtf import Form
from wtforms import StringField, TextAreaField, SelectField, PasswordField, SubmitField, FileField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Length, EqualTo, Email

class LoginForm(Form):
    usertype = SelectField( u'类型', choices = [('teacher', u'教师'), ('student', u'学生'), ('admin', u'管理员')])
    username = StringField(u'帐号',[DataRequired(message = u"用户名不能为空")], description = '')
    password = PasswordField(u'密码',[DataRequired(message = u"密码不能为空")], description = '')
    submit = SubmitField(u'登录')

class AddStudentForm(Form):
    addtype = SelectField(u'添加方式', choices = [('single', u'单个增加'), ('batch', u'批量增加')])
    student_id = StringField(u'学生学号')
    student_file = FileField(u'学生名单')
    submit = SubmitField(u'增加')

class DeleteStudentForm(Form):
    deletetype = SelectField(u'方式', choices = [('single', u'单个删除'), ('batch', u'批量删除')])
    student_id = StringField(u'学生学号')
    student_file = FileField(u'学生名单')
    submit = SubmitField(u'删除')

class AddCourseForm(Form):
    course_name = StringField(u'课程名字', [DataRequired(message = u'课程名字不能为空')])
    time = StringField(u'上课时间')
    location = StringField(u'上课地点')
    submit = SubmitField(u'增加')

class NoticeForm(Form):
    title = StringField(u'标题', [DataRequired()])
    content = TextAreaField(u'内容', [DataRequired()])
    submit = SubmitField(u'发布')

class FileForm(Form):
    file = FileField(u'文件', [DataRequired()])
    submit = SubmitField(u'上传')

class EditForm(Form):
    name = StringField(u'姓名')
    email = StringField(u'邮箱')
    password = PasswordField(u'密码')
    confirm = PasswordField(u'确认密码', [EqualTo('password', message = u'请重复输入一致的密码')])
    submit = SubmitField(u'修改')

class CourseForm(Form):
    time = StringField(u'课程时间')
    location = StringField(u'课程地点')
    submit = SubmitField(u'修改')

class FeedbackForm(Form):
    content = TextAreaField(u'反馈一下吧', [DataRequired()])
    submit = SubmitField(u'发表')

class AddPersonForm(Form):
    addtype = SelectField(u'添加方式', choices = [('single', u'单个增加'), ('batch', u'批量增加')])
    id = StringField()
    name = StringField(u'姓名')
    email = StringField(u'邮箱')
    password = StringField(u'密码')
    file = FileField()
    submit = SubmitField(u'增加')

class DeletePersonForm(Form):
    deletetype = SelectField(u'删除方式', choices = [('single', u'单个删除'), ('batch', u'批量删除')])
    id = StringField()
    file = FileField()
    submit = SubmitField(u'删除')

class ChangePasswordForm(Form):
    selecttype = SelectField(u'类型', choices = [('admin', u'管理员'), ('teacher', u'教师'), ('student', u'学生')])
    name = StringField(u'帐号', [DataRequired(u'帐号不能为空')])
    password = StringField(u'密码', [DataRequired(u'密码不能为空')])
    submit = SubmitField(u'修改')

class SearchPageForm(Form):
    page = IntegerField(u'页码', [DataRequired()])
    submit = SubmitField(u'go')

class CheckBoxForm(Form):
    checkItem = BooleanField()
    submit = SubmitField(u'删除')