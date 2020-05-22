from flask import Flask, request, jsonify
from config import Config
from flask_pymongo import PyMongo

import os
from flask_restful import Api

app = Flask(__name__)


app.config.from_object(Config)

mongo = PyMongo(app)

api = Api(app)


from app import safeDeposit
