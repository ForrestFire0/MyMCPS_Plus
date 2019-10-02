# This is the initiation file that creates our module, here we configure our application
# Import flask
from flask import Flask
# Import sessions
from flask_session import Session
# Import the os module
from os import urandom
# Import CSRF protection
from flask_wtf.csrf import CSRFProtect

# Create the flask app
app = Flask(__name__)

# Configure the secret key, which is needed for the application
app.config['SECRET_KEY'] = 'password'
# Set the session type to filesystem because the default system won't work for our purposes
app.config['SESSION_TYPE'] = 'filesystem'
# Active sessions for the app
Session(app)
# Activate csrf protection
csrf = CSRFProtect(app)

# Import the routes here 
from gradedisplay import routes
