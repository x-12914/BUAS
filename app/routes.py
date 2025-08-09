from flask import Blueprint, request, jsonify, render_template, current_app, Response, send_from_directory
from .models import Upload
# Make tasks import optional
try:
    from .tasks import save_upload_task
    TASKS_AVAILABLE = True
except ImportError:
    TASKS_AVAILABLE = False
    def save_upload_task(task_data, metadata):
        """Fallback function when Celery is not available"""
        print("Warning: Celery not available, skipping background task")
        pass

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
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'No file provided'}), 400

        # Ensure upload directory exists
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)

        filename = f"{device_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        filepath = os.path.join(upload_folder, filename)
        
        # Save the file
        file.save(filepath)
        
        # Try to save to database, but don't fail if it doesn't work
        try:
            from . import db
            upload = Upload(
                device_id=device_id,
                filename=filename,
                metadata_file=None,
                latitude=None,
                longitude=None
            )
            db.session.add(upload)
            db.session.commit()
            print(f"Successfully saved to database: {device_id} - {filename}")
        except Exception as db_error:
            print(f"Database error (continuing anyway): {db_error}")
        
        return jsonify({
            'status': 'success',
            'filename': filename,
            'device_id': device_id,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'error': str(e)}), 500


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
    try:
        # Check authentication if provided
        auth = request.authorization
        if auth:
            if not check_auth(auth.username, auth.password):
                return authenticate()

        # Try to get data from database
        try:
            uploads = Upload.query.order_by(Upload.timestamp.desc()).all()
        except Exception as db_error:
            print(f"Database error: {db_error}")
            uploads = []

        device_map = {}

        for upload in uploads:
            device_id = upload.device_id
            if device_id not in device_map:
                device_map[device_id] = {
                    'user_id': device_id,
                    'status': 'idle',
                    'location': {
                        'lat': getattr(upload, 'latitude', None) or 6.5244,
                        'lng': getattr(upload, 'longitude', None) or 3.3792
                    },
                    'session_start': None,
                    'current_session_id': None,
                    'latest_audio': f'/api/uploads/{upload.filename}',
                    'last_seen': upload.timestamp.isoformat(),
                    'latest_timestamp': upload.timestamp,  # Keep track for comparison
                    'uploads': []
                }
            else:
                # Update last_seen if this upload is more recent
                if upload.timestamp > device_map[device_id]['latest_timestamp']:
                    device_map[device_id]['last_seen'] = upload.timestamp.isoformat()
                    device_map[device_id]['latest_audio'] = f'/api/uploads/{upload.filename}'
                    device_map[device_id]['latest_timestamp'] = upload.timestamp
            
            device_map[device_id]['uploads'].append({
                'filename': upload.filename,
                'metadata_file': getattr(upload, 'metadata_file', None) or '',
                'timestamp': upload.timestamp.isoformat()
            })

        # Clean up temporary timestamp field
        for device in device_map.values():
            del device['latest_timestamp']

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
    except Exception as e:
        print(f"Dashboard data error: {e}")
        return jsonify({
            'active_sessions_count': 0,
            'total_users': 0,
            'connection_status': 'error',
            'users': [],
            'active_sessions': [],
            'stats': {
                'total_users': 0,
                'active_sessions': 0,
                'total_recordings': 0
            },
            'error': str(e),
            'last_updated': datetime.now().isoformat()
        }), 500


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
    
    try:
        # Get file size before saving
        audio_file.seek(0, 2)  # Seek to end
        file_size = audio_file.tell()
        audio_file.seek(0)  # Reset to beginning
        
        # Save the audio file
        filename = f"{phone_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{audio_file.filename}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        # Ensure upload directory exists
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        audio_file.save(filepath)
        
        # Create upload record in database with error handling
        try:
            from . import db
            upload = Upload(
                device_id=phone_id,
                filename=filename,
                metadata_file='',  # Will be updated when metadata is uploaded
                latitude=None,  # Could be extracted from metadata later
                longitude=None
            )
            db.session.add(upload)
            db.session.commit()
        except Exception as db_error:
            print(f"Database error (continuing anyway): {db_error}")
        
        return jsonify({
            'status': 'success',
            'message': 'Audio uploaded successfully',
            'phone_id': phone_id,
            'filename': filename,
            'file_size': file_size,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'error': str(e)}), 500


# ========== SESSION MANAGEMENT ENDPOINTS ==========

@routes.route('/api/start-listening/<user_id>', methods=['POST'])
def start_listening(user_id):
    """Start listening session for a user"""
    try:
        # For now, just acknowledge the start request
        # In a full implementation, you'd update user status in database
        return jsonify({
            'status': 'success',
            'message': f'Started listening for user {user_id}',
            'user_id': user_id,
            'session_id': f'session_{user_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"Start listening error: {e}")
        return jsonify({'error': str(e)}), 500


@routes.route('/api/stop-listening/<user_id>', methods=['POST'])
def stop_listening(user_id):
    """Stop listening session for a user"""
    try:
        # For now, just acknowledge the stop request
        # In a full implementation, you'd update user status in database
        return jsonify({
            'status': 'success',
            'message': f'Stopped listening for user {user_id}',
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"Stop listening error: {e}")
        return jsonify({'error': str(e)}), 500
