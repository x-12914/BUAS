from .models import db, Upload
from flask import current_app
import json, os
from datetime import datetime
from app import create_app, make_celery

app = create_app()
celery = make_celery(app)

@celery.task()
def save_upload(file_data, metadata):
    try:
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file_data['filename'])
        with open(filepath, 'wb') as f:
            f.write(file_data['data'])

        metadata_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_data['metadata_filename'])
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)

        entry = Upload(
            device_id=metadata.get("device_id"),
            filename=file_data['filename'],
            metadata_file=file_data['metadata_filename'],
            start_time=metadata.get("start_timestamp"),
            end_time=metadata.get("end_timestamp"),
            latitude=metadata.get("latitude"),
            longitude=metadata.get("longitude")
        )
        db.session.add(entry)
        db.session.commit()
    except Exception as e:
        print("Failed to process upload:", e)