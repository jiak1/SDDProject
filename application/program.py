from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

#PROJECT_ROOT = "sqlite:///"+os.path.dirname(os.path.realpath(__file__))+"/database/data.db"
PROJECT_ROOT = "mysql+pymysql://sddusername:sddpassword@database-main-serverlist.ctez1f8dx3zl.us-east-2.rds.amazonaws.com/sddmajorproject"
#PROJECT_ROOT= "mysql://sddusername:sddpassword@db4free.net/sddproject"
#PROJECT_ROOT = "mysql://jiak1_username:Password@johnny.heliohost.org/jiak1_sddprojectdb"

db = SQLAlchemy()
login = LoginManager()
login.login_view = 'PageRoutes.loginPage'
migrate = Migrate()


def create_app():
	"""Construct the core application."""
	app = Flask(__name__,static_url_path="", static_folder="static")
	app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
	app.config['SQLALCHEMY_DATABASE_URI'] = PROJECT_ROOT
	app.config['DEBUG']=True
	app.secret_key = 'super secret key'

	db.init_app(app)
	login.init_app(app)

	migrate.init_app(app, db)

	with app.app_context():
		# Import
		from .PageRoutes import PageRoutes
		from .APIRoutes import apiRoutes
		app.register_blueprint(PageRoutes)
		app.register_blueprint(apiRoutes)

		# Create tables for our models
		db.create_all()

		return app