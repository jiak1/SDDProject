from .models import Account, Course,Slide,Section

def findProblem(CID,sectionID,slideID):
	c = Course.query.filter_by(id=CID).first()
	return c.getSlide(sectionID,slideID)