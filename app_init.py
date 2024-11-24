from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from aevo_client import AevoClient
import os

app = Flask(__name__, static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'a_very_secret_key'
db = SQLAlchemy(app)

aevo_client = AevoClient(
    signing_key=os.environ.get("AEVO_SIGNING_KEY"),
    wallet_address=os.environ.get("WALLET_ADDRESS"),
    api_key=os.environ.get("AEVO_API_KEY"),
    api_secret=os.environ.get("AEVO_API_SECRET"),
    env=os.environ.get("ENV", "mainnet")
)

def create_app():
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
    app.config['SECRET_KEY'] = 'a_very_secret_key'
    return app