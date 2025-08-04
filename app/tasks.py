from .models import db, Upload
from flask import current_app
import json, os
from .celery_app import celery

@celery.task()
def save_upload(file_data, metadata):
    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']

        filepath = os.path.join(upload_folder, file_data['filename'])
        # If you trust the file is saved already, you can skip reading and rewriting:
        # But if you want to overwrite/update:
        with open(filepath, 'rb') as f:
            file_bytes = f.read()

        with open(filepath, 'wb') as f:
            f.write(file_bytes)

        metadata_path = os.path.join(upload_folder, file_data['metadata_filename'])
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
        current_app.logger.error(f"Failed to process upload: {e}")
        raise
