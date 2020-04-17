# Import flask and template operators
from flask import Flask, render_template

# Define the WSGI application object
app = Flask(__name__)

@app.route("/")
def root():
    return "fart"

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

from . import routes