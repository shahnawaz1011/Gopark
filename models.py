from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    firebase_uid = db.Column(db.String(128), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(80))
    
    # Relationships
    spots = db.relationship('ParkingSpot', backref='owner', lazy=True)
    bookings = db.relationship('Booking', backref='user', lazy=True)

class ParkingSpot(db.Model):
    __tablename__ = 'parking_spots'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    capacity = db.Column(db.Integer)
    available = db.Column(db.Integer)
    price_per_hour = db.Column(db.Float)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    sqft = db.Column(db.Float)
    vehicle_type = db.Column(db.String(100))
    available_from = db.Column(db.String(50))
    available_to = db.Column(db.String(50))
    address = db.Column(db.Text)
    mobile_number = db.Column(db.String(20))
    parking_size = db.Column(db.String(50))
    facilities = db.Column(db.Text)
    parking_type = db.Column(db.String(50))

    # Relationships
    images = db.relationship('SpotImage', backref='spot', lazy=True, cascade="all, delete-orphan")
    bookings = db.relationship('Booking', backref='spot', lazy=True)

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spots.id'), nullable=False)
    vehicle_type = db.Column(db.String(50), nullable=False)
    duration_hours = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.String(50))
    end_time = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SpotImage(db.Model):
    __tablename__ = 'spot_images'
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spots.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
