from flask import request, render_template,Blueprint,redirect,flash,url_for,send_from_directory, jsonify,abort
from flask_login import current_user, login_user,logout_user, login_required
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from .program import db,login
from .models import Account, Course,Slide
import os
import shutil
from .util import findProblem

PageRoutes = Blueprint('PageRoutes', __name__)
curDir = os.path.dirname(os.path.realpath(__file__))
 
@PageRoutes.route("/",methods=['GET'])
def homePage():
	allCourses = Course.query.all()
	return render_template("index.html",courses=allCourses)

@PageRoutes.route("/login", methods=['GET','POST'])
def loginPage():
	if current_user.is_authenticated:
		return redirect(url_for("PageRoutes.profile"))
	if request.method == 'GET':
		return render_template('login.html')

	username = request.form['username']
	password = request.form['password']
	if 'remember' in request.form:
		remember = request.form['remember']
	else:
		remember = False

	account = Account.query.filter_by(username=username).first()
	if account is None or account.check_password(password)==False:
		flash("Invalid username or password.","danger")
		return redirect(url_for("PageRoutes.loginPage"))
	login_user(account,remember=remember)

	next_page = request.form['args']
	if not next_page or url_parse(next_page).netloc != '':
		next_page = url_for('PageRoutes.homePage')
	return redirect(next_page)

@login.user_loader
def load_account(id):
	return Account.query.get(int(id))

@PageRoutes.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('PageRoutes.homePage'))

@PageRoutes.route('/profile')
@login_required
def profile():
    return "Viewing your profile"

@PageRoutes.route("/users", methods=['GET'])
@login_required
def listUsers():
	if(current_user.isAdmin == False):
		return render_template("blocked.html")
	action = request.args.get('action')
	username = request.args.get('username')
	if(action == "delete"):
		msg = "Failed to delete the account for "+username+"."
		msgType = "danger"
		try:
			user = Account.query.filter_by(username=username).first()
			db.session.delete(user)
			db.session.commit()
			msgType="success"
			msg = "Successfully deleted the account for "+username+"."
		finally:
			allUsers = Account.query.all()
			flash(msg,msgType)
			return redirect(url_for("PageRoutes.listUsers"))
	elif(action == "enableAdmin"):
		user = Account.query.filter_by(username=username).first()
		user.isAdmin = True
		db.session.commit()
		allUsers = Account.query.all()
		flash(username+" is now an administrator.","info")
		return redirect(url_for("PageRoutes.listUsers"))
	elif(action == "disableAdmin"):
		user = Account.query.filter_by(username=username).first()
		user.isAdmin = False
		db.session.commit()
		allUsers = Account.query.all()
		flash(username+" is no longer an administrator.","info")
		return redirect(url_for("PageRoutes.listUsers"))
	else:
		allUsers = Account.query.all()
	return render_template('users.html', users=allUsers)

@PageRoutes.route("/register", methods=['GET','POST'])
def register():
	if request.method == 'GET':
		return render_template('register.html')
	else:
		username = request.form['username']
		email = request.form['email']
		password = request.form['password']
		
		fail = False
		user = Account.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

		if user:
			fail = True
			msg = "An account with the email "+email+" already exists."

		user1 = Account.query.filter_by(username=username).first()

		if user1:
			fail = True
			msg = "An account with the username "+username+" already exists."
		if fail:
			flash(msg,"danger")
			return redirect(url_for("PageRoutes.register"))

		new_account = Account(username=username,email=email,isAdmin=False)
		new_account.set_password(password)
		try:
			db.session.add(new_account)
			db.session.commit()
			flash(f"Successfully registered {username}","success")
			return redirect(url_for("PageRoutes.register"))
		except:
			flash(f"Failed to register user. Please try again.","danger")
			return redirect(url_for("PageRoutes.register"))

@PageRoutes.route("/editCourse", methods=['GET','POST'])
def editCourse():
	if('action' not in request.args):
		return redirect(url_for("PageRoutes.viewCourses"))
	action = request.args['action']

	if request.method == 'POST':
		name = request.form['name']
		description = request.form['description']

		if "exists" not in request.args:
			newCourse = Course(name=name)
			db.session.add(newCourse)
		else:
			newCourse = Course.query.filter_by(id=request.args['exists']).first()
		
		newCourse.name = name
		newCourse.description = description
		db.session.commit()

		if 'imageUpload' in request.files:
			image = request.files['imageUpload']
			if image:
				try:
					os.mkdir(curDir+"/course_data/"+str(newCourse.id))
				except:
					print("0_0")
				filename = secure_filename(image.filename)
				location = os.path.join(curDir+"/course_data/"+str(newCourse.id),filename)
				image.save(location)
				newCourse.headerImageLocation = filename

				db.session.commit()
			
		return redirect(url_for("PageRoutes.viewCourses"))

	if action == "delete":
		courseID = request.args['ID']
		c = Course.query.filter_by(id=courseID).first()
		name = c.name
		try:
			loc = os.getcwd()+"/application/course_data/"+courseID+"/"
			try:
				shutil.rmtree(loc)
			except:
				random=1
			db.session.delete(c)
			db.session.commit()
			flash("Successfully Deleted "+name+".","success")
			return redirect(url_for("PageRoutes.viewCourses"))
		except:
			flash("Failed To Delete "+name+".","danger")
			return redirect(url_for("PageRoutes.viewCourses"))
	if action == "edit":
		courseID = request.args['ID']
		c = Course.query.filter_by(id=courseID).first()
		return render_template("editCourse.html",action=action,course=c,extra="&exists="+courseID)
	if action == "show" or action == "hide":
		courseID = request.args['ID']
		c = Course.query.filter_by(id=courseID).first()
		c.public = not c.public
		db.session.commit()
		if(c.public):
			flash("Released "+c.name+".","success")
		else:
			flash(c.name+" is no longer released.","danger")
		return redirect(url_for("PageRoutes.viewCourses"))
	return render_template("editCourse.html",action=action,course=None)

@PageRoutes.route("/viewCourses", methods=['GET'])
def viewCourses():
	allCourses = Course.query.all()
	return render_template("viewCourses.html",courses=allCourses)

@PageRoutes.route("/enroll", methods=['GET'])
def enroll():
	courseID = request.args['ID']
	if(current_user.inCourse(courseID) == False):
		c = Course.query.filter_by(id=courseID).first()
		if (c != None):
			current_user.joinCourse(c)
			db.session.commit()
			flash("Successfully enrolled in "+c.name+".","success")
	return redirect(url_for("PageRoutes.viewCourse")+"?ID="+courseID)

@PageRoutes.route("/static")
def images():
	filename = request.args['filename']
	directory = request.args['dir']
	loc = os.getcwd()+"/application/"+directory
	return send_from_directory(loc,filename)

@PageRoutes.route("/course")
def viewCourse():
	courseID = request.args['ID']
	c = Course.query.filter_by(id=courseID).first()

	return render_template("course.html",course=c)

@PageRoutes.route("/editProblems",methods=['POST','GET'])
def editProblems():
	courseID = request.args['ID']		
	c = Course.query.filter_by(id=courseID).first()
	if request.method == 'GET':
		return render_template("editProblems.html",course=c)
	else:
		if('action' in request.args):
			action = request.args['action']
			if(action == "NewProblem"):
				s = c.sections[0]
				p = Slide(section=s,name="New Problem")
				db.session.add(p)
				db.session.commit()
				p.orderIndex = p.id

				db.session.commit()
				response = {
					"slideid":p.id,
					"sectionid":s.id
				}
				return jsonify(response)
	return "Failure!"