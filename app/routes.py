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


@routes.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = Response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response


# ===================== API ROUTES =====================

@routes.route('/api/upload/audio/<device_id>', methods=['POST'])
def upload_audio(device_id):
    file = request.files.get('file')
    if not file:
        return 'No file provided', 400

    filename = f"{device_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    return jsonify({'filename': filename}), 200


@routes.route('/api/upload/metadata/<device_id>', methods=['POST'])
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


@routes.route('/api/audio/<device_id>/latest', methods=['GET'])
def latest_audio(device_id):
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()

    latest = (
        Upload.query
        .filter_by(device_id=device_id)
        .order_by(Upload.timestamp.desc())
        .first()
    )

    if not latest:
        return jsonify({'error': 'No recordings found'}), 404

    return jsonify({
        'filename': latest.filename,
        'url': f"/api/uploads/{latest.filename}"
    })


@routes.route('/api/dashboard-data')
def api_dashboard_data():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()

    uploads = Upload.query.order_by(Upload.timestamp.desc()).all()
    device_map = {}

    for upload in uploads:
        device_id = upload.device_id
        if device_id not in device_map:
            device_map[device_id] = {
                'user_id': device_id,
                'status': 'idle',
                'location': {
                    'lat': upload.latitude or 6.5244,
                    'lng': upload.longitude or 3.3792
                },
                'session_start': None,
                'current_session_id': None,
                'latest_audio': f'/api/uploads/{upload.filename}',
                'uploads': []
            }
        device_map[device_id]['uploads'].append({
            'filename': upload.filename,
            'metadata_file': upload.metadata_file,
            'timestamp': upload.timestamp.isoformat()
        })

    users = list(device_map.values())

    return jsonify({
        'active_sessions_count': 0,
        'total_users': len(users),
        'connection_status': 'connected',
        'users': users,
        'active_sessions': [],
        'stats': {
            'total_users': len(users),
            'active_sessions': 0,
            'total_recordings': len(uploads)
        },
        'last_updated': datetime.now().isoformat()
    })


@routes.route('/api/uploads/<filename>')
def download_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)


@routes.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })


# ========== OPTIONAL LEGACY ROUTES ==========

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
    data = [
        {
            'device_id': u.device_id,
            'metadata_file': u.metadata_file,
            'audio_file': u.filename,
            'timestamp': u.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }
        for u in uploads
    ]
    return jsonify(data)


# ========== PHONE ENDPOINTS (for dual backend architecture) ==========

@routes.route('/api/register', methods=['POST'])
def register_phone():
    """Register a new phone device"""
    data = request.get_json()
    phone_id = data.get('phone_id')
    device_name = data.get('device_name')
    
    if not phone_id:
        return jsonify({'error': 'phone_id is required'}), 400
    
    # For now, just acknowledge registration
    # In a full implementation, you'd store device info in database
    return jsonify({
        'status': 'success',
        'message': f'Phone {phone_id} registered successfully',
        'phone_id': phone_id,
        'device_name': device_name,
        'timestamp': datetime.now().isoformat()
    }), 200


@routes.route('/api/location', methods=['POST'])
def update_location():
    """Update phone location"""
    data = request.get_json()
    phone_id = data.get('phone_id')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    timestamp = data.get('timestamp')
    
    if not phone_id or latitude is None or longitude is None:
        return jsonify({'error': 'phone_id, latitude, and longitude are required'}), 400
    
    # For now, just acknowledge location update
    # In a full implementation, you'd store location in database
    return jsonify({
        'status': 'success',
        'message': f'Location updated for phone {phone_id}',
        'phone_id': phone_id,
        'latitude': latitude,
        'longitude': longitude,
        'timestamp': timestamp or datetime.now().isoformat()
    }), 200


@routes.route('/api/upload-audio', methods=['POST'])
def upload_audio_endpoint():
    """Upload audio file with authentication"""
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()
    
    phone_id = request.form.get('phone_id')
    audio_file = request.files.get('audio')
    
    if not phone_id:
        return jsonify({'error': 'phone_id is required'}), 400
    
    if not audio_file:
        return jsonify({'error': 'audio file is required'}), 400
    
    # Save the audio file
    filename = f"{phone_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{audio_file.filename}"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    
    # Ensure upload directory exists
    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    audio_file.save(filepath)
    
    # Create upload record in database
    upload = Upload(
        device_id=phone_id,
        filename=filename,
        metadata_file='',  # Will be updated when metadata is uploaded
        latitude=None,  # Could be extracted from metadata later
        longitude=None
    )
    
    from . import db
    db.session.add(upload)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Audio uploaded successfully',
        'phone_id': phone_id,
        'filename': filename,
        'file_size': len(audio_file.read()),
        'timestamp': datetime.now().isoformat()
    }), 200
