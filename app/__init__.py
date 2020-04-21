# Import flask and template operators
from flask import Flask, render_template, send_from_directory
from app.storage.sqlite import Sqlite

# Define the WSGI application object
app = Flask(__name__, static_folder="assets/")

db = Sqlite("mestorage.db")

@app.route("/")
def root():
    return "fart"

@app.route('/app/assets/<path:path>')
def send_js(path):
    return send_from_directory('assets', path)

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

from . import routes