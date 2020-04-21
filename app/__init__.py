# Import flask and template operators
from flask import Flask, render_template, send_from_directory
from app.storage.sqlite import Sqlite

# Define the WSGI application object
app = Flask(__name__, static_folder="assets/")
app.url_map.strict_slashes = False

db = Sqlite("mestorage.db")

@app.route("/")
def root():
    return render_template('games.html', gamelist=db.get_games())

@app.route('/app/assets/<path:path>')
def static_assets(path):
    return send_from_directory('assets', path)

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

from . import routes