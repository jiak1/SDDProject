from flask import request,Blueprint, jsonify,abort
from .program import db
from .models import Course,Section,Slide
from .util import findProblem

apiRoutes = Blueprint('APIRoutes', __name__)
import hmac
import hashlib

@apiRoutes.route("/api/LoadProblem",methods=['GET'])
def API_LoadProblem():
	courseID = request.args['ID']	
	sectionID = request.args['SECTIONID']
	slideID = request.args['SLIDEID']		
	_p = findProblem(courseID,sectionID,slideID)

	if _p:
		resp ={
			"name":_p.name,
			"description":_p.explanation,
			"type":_p.type,
			"video":_p.video,
			"possibleAnswers":_p.possibleAnswers,
			"correctAnswer":_p.correctAnswer
		}
		return resp
	return ""
@apiRoutes.route("/api/UpdateProblem",methods=['POST'])
def API_UpdateProblem():
	courseID = request.args['ID']	
	sectionID = request.args['SECTIONID']
	slideID = request.args['SLIDEID']		
	_p = findProblem(courseID,sectionID,slideID)
	
	if _p:
		data = request.get_json();
		_p.name = data['name']
		_p.explanation = data['description']
		_p.video = data['video']
		_p.possibleAnswers = data['possibleAnswers']
		_p.correctAnswer = data['correctAnswer']
		db.session.commit()
		resp = jsonify(success=True)
		return resp
	abort(400)

@apiRoutes.route("/api/DeleteProblem",methods=['GET'])
def API_DeleteProblem():
	courseID = request.args['ID']	
	sectionID = request.args['SECTIONID']
	slideID = request.args['SLIDEID']		
	_p = findProblem(courseID,sectionID,slideID)
	
	if _p:
		db.session.delete(_p)
		db.session.commit()
		resp = jsonify(success=True)
		return resp
	abort(400)

@apiRoutes.route("/api/AddSection",methods=['GET'])
def API_AddSection():
	courseID = request.args['ID']	
	c = Course.query.filter_by(id=courseID).first()

	s = Section(course=c,name="New Section")
	db.session.add(s)
	db.session.commit()
	s.orderIndex = s.id
	db.session.commit()

	resp = jsonify({"sectionid":s.id})
	return resp

@apiRoutes.route("/api/LoadSection",methods=['GET'])
def API_LoadSection():
	courseID = request.args['ID']	
	sectionID = request.args['SECTIONID']
	c = Course.query.filter_by(id=courseID).first()
	section = c.getSection(sectionID);

	if section:
		resp ={
			"name":section.name
		}
		return resp
	return ""

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
	abort(400)

@apiRoutes.route("/api/MoveSlideInSection",methods=['GET'])
def API_ModeSlideInSection():
	courseID = request.args['ID']	
	sectionID = request.args['SECTIONID']
	slideID = request.args['SLIDEID']
	newIndex = request.args['NEWINDEX']

	c = Course.query.filter_by(id=courseID).first()
	slide = c.getSlide(sectionID,slideID);
	section = c.getSection(sectionID)


	if slide and section:
		oldIndex = section.orderIndex;
		section.slides[oldIndex].orderIndex
		section.orderIndex = newIndex
		db.session.commit()
		resp = jsonify(success=True)
		return resp
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
		print(str(oldSection.orderIndex)+":"+str(inWaySection.orderIndex))

		direct = ""
		if oldSection.orderIndex < inWaySection.orderIndex:
			direct = "MOVEUP" #The section is dragging down so we need to move all the others up out of its way
		oldSection.orderIndex = inWaySection.orderIndex #The moved item takes the spot of the item that way previously there
		db.session.commit()
		moveOrder(inWaySection,c,direct)
		db.session.commit()

		return jsonify(success=True)
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
			print(status)
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
	courseID = request.args['ID']	
	slideID = request.args['SLIDEID']		
	_s = Slide.query.filter_by(id=slideID).first()
	
	if _s:
		data = request.get_json();
		_s.type = data['type']
		db.session.commit()
		resp = jsonify(success=True)
		return resp
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
				print(slide.name)
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
			"possibleAnswers":foundSlide.possibleAnswers
		}
		return response
	abort(400)


@apiRoutes.route("/api/CheckQuizAnswer",methods=['POST'])
def API_CheckQuizAnswer():
	courseID = request.args['ID']	
	problemNum = int(request.args['PROBLEMNUM'])
	course = Course.query.get(int(courseID));

	found = False
	foundSlide = None
	currentNum = 1

	for section in course.sections:
		for slide in section.slides:
			if(found):
				break

			if(currentNum == problemNum):
				found = True
				foundSlide = slide
			currentNum += 1

	if found:
		return {
			"correctAnswers":foundSlide.correctAnswer
		}
	abort(400)
