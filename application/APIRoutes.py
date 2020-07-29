from flask import request,Blueprint, jsonify,abort
from .program import db
from .models import Course,Section,Slide,Question,Answer
from .util import findProblem

#Create blueprint so that the pages can be registered in the main program
apiRoutes = Blueprint('APIRoutes', __name__)

#Hasing libraries
import hmac
import hashlib

#API Request sent when a user clicks on a slide to load it
@apiRoutes.route("/api/LoadProblem",methods=['GET'])
def API_LoadProblem():
	#Get the header elements sent with the GET request, in the form of a dictionary
	courseID = request.args['ID']	
	sectionID = request.args['SECTIONID']
	slideID = request.args['SLIDEID']

	#Get problem details from the relevant IDS and check it exists		
	_p = findProblem(courseID,sectionID,slideID)
	if _p:
		#Create a response dictionary with the relevant info and if its a quiz add a question ID key and then send the info to the user.
		resp ={
			"name":_p.name,
			"description":_p.explanation,
			"type":_p.type,
			"video":_p.video
		}
		if(_p.type=="Quiz"):
			resp["questionID"] = _p.questions[0].id
		
		return resp
	#Return error because problem doesn't exist
	return abort(400)

#API Request sent when a user changes any details of a problem
@apiRoutes.route("/api/UpdateProblem",methods=['POST'])
def API_UpdateProblem():
	#Get the header elements sent with the POST request, in the form of a dictionary
	courseID = request.args['ID']	
	sectionID = request.args['SECTIONID']
	slideID = request.args['SLIDEID']	

	#Get problem details from the relevant IDS and check it exists		
	_p = findProblem(courseID,sectionID,slideID)
	if _p:
		#Retrieve the data posted in json from the client and set the problems details accordingly
		data = request.get_json();
		_p.name = data['name']
		_p.explanation = data['description']
		_p.video = data['video']
		db.session.commit()

		#Return a special request with the Web Code 500 (OK) so that the Javascript knows everything worked properly
		resp = jsonify(success=True)
		return resp
	#Return error because problem doesn't exist
	abort(400)

#API Request sent when a user deletes a slide
@apiRoutes.route("/api/DeleteProblem",methods=['GET'])
def API_DeleteProblem():
	#Get the header elements sent with the GET request, in the form of a dictionary
	courseID = request.args['ID']	
	sectionID = request.args['SECTIONID']
	slideID = request.args['SLIDEID']		

	#Get problem details from the relevant IDS and check it exists	
	_p = findProblem(courseID,sectionID,slideID)
	if _p:
		#Connect to the database and delete the problem
		db.session.delete(_p)
		db.session.commit()

		#Return a special request with the Web Code 500 (OK) so that the Javascript knows everything worked properly
		resp = jsonify(success=True)
		return resp
	#Return error because problem doesn't exist
	abort(400)

#API Request that returns a list of questions in a dictionary
@apiRoutes.route("/api/GetQuestionBank",methods=['GET'])
def API_GetQuestionBank():
	#Get the header elements sent with the GET request, in the form of a dictionary
	courseID = request.args['ID']	
	sectionID = request.args['SECTIONID']
	slideID = request.args['SLIDEID']		

	#Get problem details from the relevant IDS and check it exists	
	_p = findProblem(courseID,sectionID,slideID)
	if _p:
		#Loop through questions in the problem and add them to the dictionary
		questions = {}
		for q in _p.questions:
			questions[q.id] = q.name

		#Return the dictionary in JSON format
		return jsonify(questions)
	#Return error because problem doesn't exist
	abort(400)

#API request that takes in a section and slide and will add a brand new question to the question bank on the slide
@apiRoutes.route("/api/AddQuestionToBank",methods=['GET'])
def API_AddQuestionToBank():
	#Get the header elements sent with the GET request, in the form of a dictionary
	courseID = request.args['ID']	
	sectionID = request.args['SECTIONID']
	slideID = request.args['SLIDEID']

	#Get problem details from the relevant IDS and check it exists	
	_p = findProblem(courseID,sectionID,slideID)
	if _p:
		#Create a brand new question, set its parent slide with the foreign key and add it to the database
		question = Question(slide=_p,explanation="",name="New Question")

		db.session.add(question)
		db.session.commit()

		#Return the question ID
		return str(question.id)
	#Return error because problem doesn't exist
	abort(400)

#API page that will take in a list of Answers in JSON format and update the slide with the new details
@apiRoutes.route("/api/UpdateQuestionBankAnswers",methods=['POST'])
def API_UpdateQuestionBankAnswers():
	#Get the header question ID sent with the POST request
	questionID = request.args['QID']	

	#Try and get the question with the given ID from the database and check it exists
	_q = Question.query.get(int(questionID))
	if _q:
		#Loop through the current answers in the slides question bank and delete them
		#Have to do it this way because there is not an easy way of checking if an answer has changed and the MYSQL query is only sent when commit() is called hence it isn't as innefficient as it seems
		for answer in _q.answers:
			db.session.delete(answer)
		
		#Loop through questions and add them to slide in database, sent as JSON
		data = request.get_json();

		for element in data:
			_answer = Answer(question=_q,name=element['name'],correct=element['correct'])
			db.session.add(_answer)
		db.session.commit()

		#Return a success code 500 (OK)
		return jsonify(success=True)
	#Return error because problem doesn't exist
	abort(400)

#API route for getting a questions details that is in a question bank
@apiRoutes.route("/api/GetQuestionBankQuestion",methods=['GET'])
def API_GetQuestionBankQuestion():
	#Get the question ID from the request header
	questionID = request.args['QuestionID']	

	#Try and get the question with the given ID from the database and check it exists
	_q = Question.query.get(int(questionID))
	if _q:
		#Create a dictionary and set its values to those from the database
		response = {
			"explanation":_q.explanation,
			"name":_q.name,
			"answers":[]
		}

		#Loop through the database and add the questions answers accordingly to the dictionary
		for answer in _q.answers:
			response["answers"].append({
				"name":answer.name,
				"correct":answer.correct
			})

		#Return the constructed dictionary
		return response
	#Return error because problem doesn't exist
	abort(400)

#API route for updating a question bank question
@apiRoutes.route("/api/UpdateQuestionBankQuestion",methods=['POST'])
def API_UpdateQuestionBankQuestion():
	#Get the question ID from the POST request header, set by the AJAX request
	questionID = request.args['QID']

	#Try and get the question with the given ID from the database and check it exists
	_q = Question.query.get(int(questionID))
	if _q:
		#Get the JSON passed with the request and set the question bank questions details accordingly and save to the database
		data = request.get_json();

		_q.name = data['name']
		_q.explanation = data['explanation']
		db.session.commit()

		return jsonify(success=True)
	#Return error because problem doesn't exist
	abort(400)

#API route for deleting a question in a question bank
@apiRoutes.route("/api/DeleteQuestionBankQuestion",methods=['GET'])
def API_DeleteQuestionBankQuestion():
	#Get the Question ID passed in as a header in the GET request
	questionID = request.args['QID']	

	#Try and get the question with the given ID from the database and check it exists
	_q = Question.query.get(int(questionID))
	if _q:
		#Loop through each answer and delete them from the database first (Have to do this as they are in a seperate table)
		for a in _q.answers:
			db.session.delete(a)

		#Delete question from database and save
		db.session.delete(_q)
		db.session.commit()

		return jsonify(success=True)
	#Return error because problem doesn't exist
	abort(400)

#API route for adding a new section to a course
@apiRoutes.route("/api/AddSection",methods=['GET'])
def API_AddSection():
	#Get the course ID from the request header
	courseID = request.args['ID']	
	#Try and find the course by the ID
	c = Course.query.filter_by(id=courseID).first()
	
	#Create a new section with the default name and course foreign key and save it to the database
	s = Section(course=c,name="New Section")
	db.session.add(s)
	db.session.commit()
	s.orderIndex = s.id
	db.session.commit()

	#Return a JSON response with the new sections ID
	resp = jsonify({"sectionid":s.id})
	return resp

#API route for loading a sections details when selected
@apiRoutes.route("/api/LoadSection",methods=['GET'])
def API_LoadSection():
	#Gather the course ID and section ID from the request headers
	courseID = request.args['ID']	
	sectionID = request.args['SECTIONID']

	#Try and get the course and relevant section from the database
	c = Course.query.filter_by(id=courseID).first()
	section = c.getSection(sectionID);

	#If the section exists return its name
	if section:
		resp ={
			"name":section.name
		}
		return resp
	#Return error code because problem doesn't exist
	return abort(400)

#API route for updating a sections details (only name at this point)
@apiRoutes.route("/api/UpdateSection",methods=['POST'])
def API_UpdateSection():
	courseID = request.args['ID']	
	sectionID = request.args['SECTIONID']

	c = Course.query.filter_by(id=courseID).first()
	section = c.getSection(sectionID);
	
	if section:
		data = request.get_json();
		section.name = data['name']
		db.session.commit()
		resp = jsonify(success=True)
		return resp
	#Return error code because problem doesn't exist
	abort(400)

@apiRoutes.route("/api/DeleteSection",methods=['GET'])
def API_DeleteSection():
	courseID = request.args['ID']	
	sectionID = request.args['SECTIONID']

	c = Course.query.filter_by(id=courseID).first()
	section = c.getSection(sectionID);
	
	if section:
		for slide in section.slides:
			db.session.delete(slide)
		db.session.delete(section)
		db.session.commit()
		resp = jsonify(success=True)
		return resp
	#Return error code because problem doesn't exist
	abort(400)

@apiRoutes.route("/api/MoveSlide",methods=['GET'])
def API_ModeSlide():
	courseID = request.args['ID']	
	newSectionID = request.args['NEWSECTIONID']
	oldSectionID = request.args['OLDSECTIONID']
	slideID = request.args['SLIDEID']

	c = Course.query.filter_by(id=courseID).first()
	slide = c.getSlide(oldSectionID,slideID);
	newSection = c.getSection(newSectionID);
	
	if slide and newSection:
		slide.section = newSection
		db.session.commit()
		resp = jsonify(success=True)
		return resp
	#Return error code because problem doesn't exist
	abort(400)


@apiRoutes.route("/api/MoveSection",methods=['GET'])
def API_ModeSection():
	courseID = request.args['ID']	
	oldSectionID = request.args['OLDSECTIONID']
	newSectionID = request.args['NEWSECTIONID']

	c = Course.query.filter_by(id=courseID).first()
	oldSection = c.getSection(oldSectionID)
	inWaySection = c.getSection(newSectionID)

	if oldSection and inWaySection:

		direct = ""
		if oldSection.orderIndex < inWaySection.orderIndex:
			direct = "MOVEUP" #The section is dragging down so we need to move all the others up out of its way
		oldSection.orderIndex = inWaySection.orderIndex #The moved item takes the spot of the item that way previously there
		db.session.commit()
		moveOrder(inWaySection,c,direct)
		db.session.commit()

		return jsonify(success=True)
	#Return error code because problem doesn't exist
	abort(400)

def moveOrder(_section,_course,_direction):
	if _direction == "MOVEUP":
		moveIndex = _section.orderIndex-1
	else:
		moveIndex = _section.orderIndex+1

	inWaySection = _course.getSectionByOrder(moveIndex)

	_section.orderIndex = moveIndex

	if inWaySection:
		moveOrder(inWaySection,_course,_direction)
import json
@apiRoutes.route("/api/PatreonUpdate",methods=['POST'])
def API_PatreonUpdate():
	event = request.headers.get('X-Patreon-Event')
	signature = request.headers.get('X-Patreon-Signature')

	if event and signature and verifyPatreonSignature(request,signature):
		info = request.get_json();
		if(event == "members:create"):
			status = info['data']['attributes']['patron_status']

		with open('data.txt', 'w') as outfile:
			json.dump(info, outfile)
		return jsonify(success=True)
	return jsonify(success=False)

#Patreon Secret Key
secret = b"D80yIRVRs99Ip6Jc0LDZqS3eZUMqACWj9jElUzu8-LUmRNREJxmnIVQklObxH_sv"
def verifyPatreonSignature(_request,_signature):
	digest = hmac.new(secret,_request.get_data(),digestmod=hashlib.md5).hexdigest()

	if(digest == _signature):
		return True
	return False

@apiRoutes.route("/api/UpdateSlideType",methods=['POST'])
def API_ChangeSlideType():
	slideID = request.args['SLIDEID']		
	_s = Slide.query.filter_by(id=slideID).first()
	
	if _s:
		data = request.get_json();
		_s.type = data['type']
		db.session.commit()
		resp = {}
		if(_s.type=="Quiz"):
			resp["questionID"] = _s.questions[0].id

		return resp
	#Return error code because problem doesn't exist
	abort(400)


@apiRoutes.route("/api/GetSlide",methods=['POST'])
def API_GetSlide():
	courseID = request.args['ID']	
	problemNum = int(request.args['PROBLEMNUM'])
	course = Course.query.get(int(courseID));

	found = False
	foundSlide = None
	currentNum = 1
	hasNext = False
	for section in course.sections:
		for slide in section.slides:
			if(found):
				hasNext = True
				break

			if(currentNum == problemNum):
				found = True
				foundSlide = slide
			currentNum += 1

	hasPrevious = True
	if(problemNum == 1):
		hasPrevious = False

	if found:
		response = {
			"name":foundSlide.name,
			"explanation":foundSlide.explanation,
			"type":foundSlide.type,
			"video":foundSlide.video,
			"hasNext":hasNext,
			"hasPrevious":hasPrevious,
			"id":foundSlide.id
		}
		return response
	#Return error code because problem doesn't exist
	abort(400)


@apiRoutes.route("/api/CheckQuizAnswer",methods=['POST'])
def API_CheckQuizAnswer():
	questionID = request.args['QID']	
	_q = Question.query.get(int(questionID))

	if _q:
		resp = []
		for question in _q.questions:
			resp.append(question.correct)
		return jsonify(resp)
	#Return error code because problem doesn't exist
	abort(400)

@apiRoutes.route("/api/GetSlideQuestions",methods=['GET'])
def API_GetSlideQuestions():
	slideID = request.args['SLIDEID']	
	_s = Slide.query.get(int(slideID))

	if _s:
		resp = []
		for question in _s.questions:
			q = {"name":question.name,"answers":[]}
			if(_s.type == "Quiz"):
				q["explanation"]=_s.explanation
			else:
				q["explanation"]=question.explanation

			for answer in question.answers:
				q["answers"].append(answer.name)
			resp.append(q)

		return jsonify(resp)
	#Return error code because problem doesn't exist
	abort(400)

@apiRoutes.route("/api/SetSectionSlides",methods=['POST'])
def API_SetSectionSlides():
	courseID = request.args['ID']	
	sectionID = request.args['SECTIONID']
	c = Course.query.filter_by(id=courseID).first()
	section = c.getSection(sectionID);

	if section:
		data = request.get_json();
		i = 1

		for item in data['list']:
			slide = Slide.query.get(int(item))
			slide.orderIndex = i
			i += 1
		db.session.commit();
		return jsonify(success=True)
	#Return error code because problem doesn't exist
	abort(400)

@apiRoutes.route("/api/GetQuizAnswers",methods=['GET'])
def API_GetQuizAnswers():
	slideID = request.args['SLIDEID']	
	_s = Slide.query.get(int(slideID))

	if _s:
		resp = {"answers":[],"type":_s.type}
		for question in _s.questions:
			q = []
			for answer in question.answers:
				q.append(answer.correct)
			resp["answers"].append(q)
		print(resp)
		return jsonify(resp)
	#Return error code because problem doesn't exist
	abort(400)