from __future__ import absolute_import

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
CORS(app)
app.config.from_object('config')

db = SQLAlchemy(app)

migrate = Migrate(app, db)
