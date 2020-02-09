from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import os

#PROJECT_ROOT = "sqlite:///"+os.path.dirname(os.path.realpath(__file__))+"/database/data.db"
PROJECT_ROOT = "mysql://n6s5P256I6:vnCPTna4cH@remotemysql.com/n6s5P256I6"

db = SQLAlchemy()
login = LoginManager()
login.login_view = 'myApp.loginPage'
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
		from .routes import myApp
		app.register_blueprint(myApp)

		# Create tables for our models
		db.create_all()

		return app