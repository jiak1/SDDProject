from .program import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.sql import func;

courseStudents = db.Table('courseStudents',
    db.Column('accountID', db.Integer, db.ForeignKey('account.id')),
    db.Column('courseID', db.Integer, db.ForeignKey('course.id'))
)

class Account(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(20),index=True,unique=True, nullable=False) #Limited to 20 chars
	email = db.Column(db.String(120),index=True, unique=True, nullable=False)
	password_hash = db.Column(db.String(128),nullable=False)
	isAdmin = db.Column(db.Boolean,default=0,nullable=False)
	accountCreateDate = db.Column(db.DateTime,nullable=False,default=func.now())

	courses = db.relationship('Course',secondary=courseStudents, backref=db.backref('students'),lazy="dynamic")

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)

	def __repr__(self):
		return (f"Created {self.username}'s account")

	def joinCourse(self, course):
		if not self.inCourse(course.id):
			self.courses.append(course)

	def leaveCourse(self, course):
		if self.inCourse(course.id):
			self.courses.remove(course)

	def inCourse(self, courseID):
		return self.courses.filter(courseStudents.c.accountID == courseID).count() > 0

class Course(db.Model):

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(40),index=True,nullable=False)
	description = db.Column(db.Text())
	headerImageLocation = db.Column(db.Text(), nullable=True, default="")
	courseCreateDate = db.Column(db.DateTime,nullable=False,default=func.now())
	
	public = db.Column(db.Boolean,default=0,nullable=False)
	#also has course.students which returns a list of all enrolled students
	def __repr__(self):
		return "Created new course!"