from . import db
from datetime import datetime

class Upload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(100), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    metadata_file = db.Column(db.String(200), nullable=False)
    start_time = db.Column(db.BigInteger)
    end_time = db.Column(db.BigInteger)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
