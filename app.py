from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from models import db, User, ParkingSpot, Booking, SpotImage
from flask_migrate import Migrate
import firebase_admin
from firebase_admin import credentials, auth

app = Flask(__name__)
# A secret key is required for Flask to manage user login sessions securely
app.secret_key = 'your_super_secret_developer_key' 
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

# Firebase Initialization
cred_path = os.path.join(app.root_path, 'serviceAccountKey.json')
try:
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    else:
        print("Warning: serviceAccountKey.json not found for Firebase Admin.")
except Exception as e:
    print("Warning: Firebase Admin SDK initialization error.", e)

def init_db():
    with app.app_context():
        db.create_all()
        
        # Check if we already have data
        if ParkingSpot.query.first() is None:
            # Updated dummy data coordinates to match your map's location
            dummy_data = [
                ParkingSpot(name='Station Road Parking', lat=17.6750, lng=75.9050, capacity=100, available=23, price_per_hour=50.0, sqft=2000, vehicle_type='Car,Bike', available_from='2020-01-01T00:00', available_to='2030-01-01T00:00', address='Station Road, Pune', mobile_number='9876543210', parking_size='Fullsize', facilities='Gated,CCTV camera', parking_type='Parking Lot'),
                ParkingSpot(name='Navi Peth Secure Park', lat=17.6680, lng=75.9000, capacity=50, available=5, price_per_hour=30.0, sqft=1000, vehicle_type='Car', available_from='2020-01-01T00:00', available_to='2030-01-01T00:00', address='Navi Peth, Pune', mobile_number='9876543211', parking_size='Compact SUV', facilities='CCTV camera', parking_type='Apartment'),
                ParkingSpot(name='Market Yard Auto Stand', lat=17.6550, lng=75.8950, capacity=200, available=112, price_per_hour=20.0, sqft=5000, vehicle_type='Car,Bike', available_from='2020-01-01T00:00', available_to='2030-01-01T00:00', address='Market Yard, Pune', mobile_number='9876543212', parking_size='hatchback', facilities='None', parking_type='Street'),
                ParkingSpot(name='City Center Mall Parking', lat=17.6800, lng=75.9100, capacity=30, available=0, price_per_hour=100.0, sqft=500, vehicle_type='Car', available_from='2020-01-01T00:00', available_to='2030-01-01T00:00', address='City Center Mall, Pune', mobile_number='9876543213', parking_size='Fullsize', facilities='Gated,CCTV camera,Security Gaurd', parking_type='Parking Lot')
            ]
            
            for spot in dummy_data:
                db.session.add(spot)
            db.session.flush()
            
            dummy_images = [
                SpotImage(spot_id=dummy_data[0].id, filename='1_dummy_station_road.png'),
                SpotImage(spot_id=dummy_data[1].id, filename='2_dummy_navi_peth.png'),
                SpotImage(spot_id=dummy_data[2].id, filename='3_dummy_market_yard.png'),
                SpotImage(spot_id=dummy_data[3].id, filename='4_dummy_mall.png')
            ]
            for img in dummy_images:
                db.session.add(img)
                
            db.session.commit()
            print("Database initialized with dummy data and premium images.")

# --- Authentication Routes ---

@app.route('/signup', methods=['GET'])
def signup():
    return render_template('signup.html')

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@app.route('/api/sessionLogin', methods=['POST'])
def session_login():
    id_token = request.json.get('idToken')
    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        email = decoded_token.get('email', '')
        username = decoded_token.get('name') or email.split('@')[0]
        
        user = User.query.filter_by(firebase_uid=uid).first()
        
        if not user:
            # Create user
            user = User(firebase_uid=uid, email=email, username=username)
            db.session.add(user)
            db.session.commit()
            
        session['user_id'] = user.id
        session['username'] = user.username
        session['mode'] = 'driver'
        
        return jsonify({'success': True})
    except Exception as e:
        print("Auth error:", e)
        return jsonify({'success': False, 'message': 'Invalid token'}), 401

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/toggle-mode')
def toggle_mode():
    if 'user_id' in session:
        current_mode = session.get('mode', 'driver')
        session['mode'] = 'owner' if current_mode == 'driver' else 'driver'
    return redirect(request.referrer or url_for('home'))

# --- Core App Routes ---

@app.route('/')
def home():
    return render_template('index.html', username=session.get('username'), mode=session.get('mode'))

@app.route('/find')
def find_spot():
    return render_template('map.html', username=session.get('username'), mode=session.get('mode'))

@app.route('/api/parking')
def get_parking_data():
    spots = ParkingSpot.query.all()
    
    spots_data = []
    for spot in spots:
        spot_dict = {
            'id': spot.id,
            'name': spot.name,
            'lat': spot.lat,
            'lng': spot.lng,
            'capacity': spot.capacity,
            'available': spot.available,
            'price_per_hour': spot.price_per_hour,
            'owner_id': spot.owner_id,
            'sqft': spot.sqft,
            'vehicle_type': spot.vehicle_type,
            'available_from': spot.available_from,
            'available_to': spot.available_to,
            'address': spot.address,
            'mobile_number': spot.mobile_number,
            'parking_size': spot.parking_size,
            'facilities': spot.facilities,
            'parking_type': spot.parking_type,
            'images': [img.filename for img in spot.images]
        }
        spots_data.append(spot_dict)
        
    return jsonify(spots_data)

@app.route('/spot/<int:spot_id>')
def spot_detail(spot_id):
    spot = ParkingSpot.query.get(spot_id)
    
    if not spot:
        flash("Spot not found.", "error")
        return redirect(url_for('home'))
        
    spot_dict = {
        'id': spot.id,
        'name': spot.name,
        'lat': spot.lat,
        'lng': spot.lng,
        'capacity': spot.capacity,
        'available': spot.available,
        'price_per_hour': spot.price_per_hour,
        'owner_id': spot.owner_id,
        'sqft': spot.sqft,
        'vehicle_type': spot.vehicle_type,
        'available_from': spot.available_from,
        'available_to': spot.available_to,
        'address': spot.address,
        'mobile_number': spot.mobile_number,
        'parking_size': spot.parking_size,
        'facilities': spot.facilities,
        'parking_type': spot.parking_type,
        'images': [img.filename for img in spot.images]
    }
    
    return render_template('spot_details.html', spot=spot_dict, username=session.get('username'), mode=session.get('mode'))

@app.route('/api/book/<int:spot_id>', methods=['POST'])
def book_spot(spot_id):
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "You must be logged in to book a spot."}), 401

    data = request.get_json()
    vehicle_type = data.get('vehicle_type', 'Car')
    duration = int(data.get('duration', 1))
    start_time = data.get('start_time')
    end_time = data.get('end_time')

    spot = ParkingSpot.query.get(spot_id)

    if spot and spot.available > 0:
        spot.available -= 1
        
        booking = Booking(
            user_id=session['user_id'],
            spot_id=spot_id,
            vehicle_type=vehicle_type,
            duration_hours=duration,
            start_time=start_time,
            end_time=end_time
        )
        db.session.add(booking)
        db.session.commit()
        
        total_price = spot.price_per_hour * duration
        return jsonify({"success": True, "message": f"Successfully booked for {duration} hr(s)! Total cost: ₹{total_price}."})
    
    return jsonify({"success": False, "message": "Sorry, this lot is full."}), 400

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to view your dashboard.', 'error')
        return redirect(url_for('login'))

    user_id = session['user_id']
    
    # Grab user bookings
    user_bookings = db.session.query(
        Booking.id.label('booking_id'),
        Booking.vehicle_type,
        Booking.duration_hours,
        Booking.start_time,
        Booking.end_time,
        ParkingSpot.name,
        ParkingSpot.price_per_hour,
        ParkingSpot.lat,
        ParkingSpot.lng
    ).join(ParkingSpot, Booking.spot_id == ParkingSpot.id).filter(Booking.user_id == user_id).all()
    
    owner_listings = []
    owner_bookings = []
    if session.get('mode') == 'owner':
        owner_listings = ParkingSpot.query.filter_by(owner_id=user_id).all()
        
        owner_bookings = db.session.query(
            Booking.vehicle_type,
            Booking.duration_hours,
            Booking.start_time,
            Booking.end_time,
            ParkingSpot.name.label('spot_name'),
            ParkingSpot.price_per_hour,
            User.username.label('driver_name')
        ).join(ParkingSpot, Booking.spot_id == ParkingSpot.id).join(User, Booking.user_id == User.id).filter(ParkingSpot.owner_id == user_id).all()
        
    return render_template('dashboard.html', username=session.get('username'), mode=session.get('mode'), bookings=user_bookings, listings=owner_listings, owner_bookings=owner_bookings)

@app.route('/rent-spot-intent')
def rent_spot_intent():
    if 'user_id' not in session:
        flash('It is mandatory to sign up for renting a spot.', 'error')
        return redirect(url_for('signup'))
    
    session['mode'] = 'owner'
    return redirect(url_for('list_space'))

@app.route('/list-space', methods=['GET', 'POST'])
def list_space():
    if 'user_id' not in session or session.get('mode') != 'owner':
        flash('Only owners in Owner Mode can list spaces.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form.get('name')
        lat = request.form.get('lat')
        lng = request.form.get('lng')
        capacity = request.form.get('capacity')
        sqft = request.form.get('sqft')
        vehicle_type = request.form.get('vehicle_type')
        available_from = request.form.get('available_from')
        available_to = request.form.get('available_to')
        price_per_hour = request.form.get('price_per_hour')
        address = request.form.get('address')
        mobile_number = request.form.get('mobile_number')
        parking_size = request.form.get('parking_size')
        facilities_list = request.form.getlist('facilities')
        facilities = ",".join(facilities_list) if facilities_list else "None"
        parking_type = request.form.get('parking_type')
        
        spot = ParkingSpot(
            name=name, lat=float(lat), lng=float(lng), capacity=int(capacity),
            available=int(capacity), price_per_hour=float(price_per_hour),
            owner_id=session['user_id'], sqft=float(sqft), vehicle_type=vehicle_type,
            available_from=available_from, available_to=available_to,
            address=address, mobile_number=mobile_number, parking_size=parking_size,
            facilities=facilities, parking_type=parking_type
        )
        db.session.add(spot)
        db.session.flush() # To get spot.id
        
        images = request.files.getlist('images')
        for file in images:
            if file and file.filename:
                filename = secure_filename(file.filename)
                filename = f"{spot.id}_{int(datetime.now().timestamp())}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                img_record = SpotImage(spot_id=spot.id, filename=filename)
                db.session.add(img_record)
                
        db.session.commit()
        flash('Spot listed successfully!', 'success')
        return redirect(url_for('dashboard'))
        
    return render_template('list_space.html', username=session.get('username'), mode=session.get('mode'))

@app.route('/api/cancel_booking/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    if 'user_id' not in session:
        flash('Please log in to cancel a booking.', 'error')
        return redirect(url_for('login'))

    booking = Booking.query.filter_by(id=booking_id, user_id=session['user_id']).first()
    
    if booking:
        spot = ParkingSpot.query.get(booking.spot_id)
        if spot:
            spot.available += 1
        db.session.delete(booking)
        db.session.commit()
        flash('Booking cancelled successfully', 'success')
    else:
        flash('Booking not found or unauthorized.', 'error')

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
    