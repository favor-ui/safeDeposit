from flask import Flask, request, jsonify
from config import Config
from flask_pymongo import PyMongo

import os
from flask_restful import Api

app = Flask(__name__)


app.config.from_object(Config)
# db = SQLAlchemy(app)
mongo = PyMongo(app)
mongo2 = PyMongo(app, os.environ.get('MONGO_URI_2'))
api = Api(app)

redis = FlaskRedis(app)

from app import safeDeposit
