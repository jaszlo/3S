from flask import Flask, render_template, request, make_response, Response
from functools import wraps
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import threading

DEBUG = True

app = Flask(__name__)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
) 

# Credentials
import config

from db import Database
db = Database()
app = Flask(__name__)



def check_auth(username, password):
    return username == config.USERNAME and password == config.PASSWORD


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return Response(
                "Could not verify your access level for that URL.\n"
                "You have to login with proper credentials", 401,
                {"WWW-Authenticate": 'Basic realm="Login Required"'})
        return f(*args, **kwargs)
    return decorated

@app.route("/", methods=["GET"])
@limiter.limit("10 per minute")
@requires_auth
def index():
    return render_template("upload.html")

@app.route("/upload", methods=["POST"])
@limiter.limit("10 per minute")
@requires_auth
def handle_upload():
    if "file" not in request.files:
        return "No file part"
    
    file = request.files["file"]
    file_extension = file.filename.split(".")[-1]

    if file.filename == "":
        return "No selected file"
    
    if file_extension not in config.ALLOWED_IMAGE_EXTENSIONS:
        return "Invalid file type"

    if file:
        bytes = b"".join(file.stream.readlines())
        id = db.insert_image(file.filename, bytes)
        return f'{{"status": "success", "filename": "{file.filename}", "id": "{id}"}}'


@app.route("/list")
@requires_auth
def list_images():
    result = db.get_images()
    entries = []
    
    print(len(result))
    for result in result:
        entries.append({"id": result[0], "filename": result[1], "size": f'{result[2] / 1000} kB', "url": f"/i/{result[0]}"})
    #return entries
    return render_template("list.html", entries=entries)


@app.route("/i/<image_id>")
@limiter.limit("10 per minute")
def image(image_id):
    result, success = db.get_image(int(image_id))
    if not success:
        return "Image not found", 404
    
    filename, bytes = result
    file_extension = filename.split(".")[-1]

    response = make_response(bytes)
    response.headers.set("Content-Type", f"image/{file_extension}")
    return response    

def cyclic_cleanup():
    threading.Timer(config.CYCLIC_CLEANUP_INTERVAL, cyclic_cleanup).start()
    db.clear()

if __name__ == "__main__":
    threading.Timer(config.CYCLIC_CLEANUP_INTERVAL, cyclic_cleanup).start()
    app.run(debug=True)
    
