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
	username = db.Column(db.String(20), nullable=False) #Limited to 20 chars
	email = db.Column(db.String(120), nullable=False)
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
		return self.courses.filter(courseStudents.c.courseID == courseID).count() > 0

class Course(db.Model):

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(40),index=True,nullable=False)
	description = db.Column(db.Text())
	headerImageLocation = db.Column(db.Text(), nullable=True, default="")
	courseCreateDate = db.Column(db.DateTime,nullable=False,default=func.now())
	sections = db.relationship("Section",backref="course",order_by="Section.orderIndex")

	public = db.Column(db.Boolean,default=0,nullable=False)
	#also has course.students which returns a list of all enrolled students
	def __repr__(self):
		return "Created new course!"

	def getSection(self, SID):
		SID = int(SID)
		for _sect in self.sections:
			if (_sect.id == SID):
				return _sect
		return None

	def getSectionByOrder(self, SID):
		SID = int(SID)
		for _sect in self.sections:
			if (_sect.orderIndex == SID):
				return _sect
		return None
	
	def listSections(self):
		print("START ----")
		for s in self.sections:
			print(s.name+":"+str(s.orderIndex))
		print("---- END")
	
	def getSlide(self, sectionID, slideID):
		return self.getSection(sectionID).getSlide(slideID)

class Section(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	orderIndex = db.Column(db.Integer)
	courseid = db.Column(db.Integer,db.ForeignKey("course.id"))
	name = db.Column(db.String(30))
	slides = db.relationship("Slide",backref="section")
	
	def getSlide(self, SID):
		SID = int(SID)
		for _slide in self.slides:
			if (_slide.id == SID):
				return _slide
		return None
	
	def setOrderIndex(self):
		self.orderIndex=self.getNextSlideIndex()
		
class Slide(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	orderIndex = db.Column(db.Integer)
	sectionid = db.Column(db.Integer,db.ForeignKey("section.id"))
	explanation = db.Column(db.Text())
	name = db.Column(db.String(30))
	video = db.Column(db.String(50),default="")
	type = db.Column(db.String(15), default="Info")
	
	possibleAnswers = db.Column(db.Text())
	correctAnswer = db.Column(db.Text())