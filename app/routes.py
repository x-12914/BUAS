from flask import Blueprint, request, jsonify, render_template, current_app, Response, send_from_directory
from .models import Upload
from .tasks import save_upload_task
from datetime import datetime
import os

routes = Blueprint('routes', __name__)

def check_auth(username, password):
    return username == "admin" and password == "supersecret"

def authenticate():
    return Response("Unauthorized", 401, {"WWW-Authenticate": 'Basic realm="Login Required"'})

@routes.route('/upload/audio/<device_id>', methods=['POST'])
def upload_audio(device_id):
    file = request.files.get('file')
    if not file:
        return 'No file provided', 400

    filename = f"{device_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    return jsonify({'filename': filename}), 200

@routes.route('/upload/metadata/<device_id>', methods=['POST'])
def upload_metadata(device_id):
    metadata = request.get_json()
    filename = metadata.get("filename")
    metadata_filename = f"{device_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_meta.json"

    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return "Audio file not found", 404

    with open(filepath, 'rb') as f:
        file_data = f.read()

    task_data = {
        'filename': filename,
        'metadata_filename': metadata_filename,
        'data': file_data
    }
    metadata['device_id'] = device_id

    save_upload_task(task_data, metadata)

    return 'Metadata queued for saving', 200

@routes.route('/dashboard')
def dashboard():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()
    return render_template('dashboard.html')

@routes.route('/dashboard/data')
def dashboard_data():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()

    uploads = Upload.query.order_by(Upload.timestamp.desc()).all()
    data = [{
        'device_id': u.device_id,
        'metadata_file': u.metadata_file,
        'audio_file': u.filename,
        'timestamp': u.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    } for u in uploads]
    return jsonify(data)

@routes.route('/uploads/<filename>')
def download_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
