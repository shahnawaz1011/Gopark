# 🚗 GoPark - Smart Parking Solution

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Flask Version](https://img.shields.io/badge/flask-3.1.3-green.svg)](https://flask.palletsprojects.com/)
[![Firebase Auth](https://img.shields.io/badge/firebase-auth-orange.svg)](https://firebase.google.com/)
[![Database](https://img.shields.io/badge/database-sqlite-lightgrey.svg)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

GoPark is a premium, full-stack smart parking application built to connect drivers searching for convenient parking with landowners/spot owners looking to monetize their empty spaces. Powered by Flask, SQLAlchemy, Firebase Authentication, and interactive Leaflet maps, GoPark bridges the gap of urban congestion and makes parking stress-free.

---

## 🌟 Key Features

### 👤 Dual-Persona Dashboard
GoPark supports two modes seamlessly toggled from the user interface:
*   **Driver Mode (Find & Book):**
    *   Interactive Leaflet Map to locate nearby parking spots in real-time.
    *   Search by city, area, or current location.
    *   Detailed spot descriptions including price-per-hour, parking size compatibility, facilities, timing availability, and photo galleries.
    *   Instant reservation booking with cost estimation.
    *   Booking management dashboard to view history or cancel active bookings.
*   **Owner Mode (Host & Earn):**
    *   List empty driveways, garages, lots, or commercial spaces.
    *   Rich-form fields to specify coordinates, dimensions, pricing, and upload multiple photos.
    *   Earnings tracker and tenant booking management console to monitor who is parked where and when.

### 🔒 Firebase Authentication
*   Fully integrated Firebase Authentication (Email/Password, Google Sign-in) on the client.
*   Secure Token Verification on the backend via Firebase Admin SDK.
*   Flask Session sync to manage page accessibility and owner-driver routing.

### 🎨 Responsive Glassmorphism Design
*   Highly aesthetic, futuristic UI leveraging custom Vanilla CSS styling, subtle animations, scroll reveals, and gradient background styling.
*   TailwindCSS utilities for structured components.

---

## 📂 Project Architecture

```directory
smart-parking-app/
├── app.py                  # Core Flask server, routing, configuration, and API endpoints
├── models.py               # SQLAlchemy Database Models (User, ParkingSpot, Booking, SpotImage)
├── requirements.txt        # Python package dependencies
├── serviceAccountKey.json  # Firebase Admin Service Account credentials (Git Ignored)
├── .gitignore              # Git ignored files configuration
├── migrations/             # Database migration history (Flask-Migrate)
├── static/                 # Static assets folder
│   ├── style.css           # Custom Glassmorphic styles & animations
│   ├── script.js          # Interactive Leaflet maps & asynchronous API logic
│   ├── uploads/            # Dynamic image uploads of listed parking spaces
│   └── *.png, *.jpg        # UI assets, hero backgrounds, and brand icons
└── templates/              # HTML templates (Flask Rendering)
    ├── index.html          # Main portal with tabs for Finding or Renting spots
    ├── map.html            # Map explorer interface
    ├── login.html          # Firebase-powered Login portal
    ├── signup.html         # Firebase-powered Registration portal
    ├── dashboard.html      # Consolidated user management dashboard
    ├── list_space.html     # Landlord listing input wizard
    └── spot_details.html   # Detailed view of a parking spot with photo galleries
```

---

## 🗄️ Database Schema

The SQLite database structure is mapped via SQLAlchemy ORM into four core models:



    User {
        int id PK
        string firebase_uid UK
        string email
        string username
    }

    ParkingSpot {
        int id PK
        string name
        float lat
        float lng
        int capacity
        int available
        float price_per_hour
        int owner_id FK
        float sqft
        string vehicle_type
        string available_from
        string available_to
        text address
        string mobile_number
        string parking_size
        text facilities
        string parking_type
    }

    Booking {
        int id PK
        int user_id FK
        int spot_id FK
        string vehicle_type
        int duration_hours
        string start_time
        string end_time
        datetime created_at
    }

    SpotImage {
        int id PK
        int spot_id FK
        string filename
    }

---

## 🚀 Getting Started

### 📋 Prerequisites
Ensure you have the following installed on your system:
*   [Python 3.8+](https://www.python.org/downloads/)
*   [Git](https://git-scm.com/)

---

### 🔧 Local Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-username/smart-parking-app.git
    cd smart-parking-app
    ```

2.  **Create and Activate Virtual Environment:**
    ```bash
    # Windows (PowerShell/CMD)
    python -m venv venv
    .\venv\Scripts\activate

    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Database Setup:**
    Initialize SQLite database tables and apply seed dummy data (coordinates configured around city center Pune by default):
    ```bash
    # Runs db.create_all() and injects initial dummy spots automatically on first run
    python app.py
    ```

---

### 🔑 Firebase Admin Integration Setup

To enable user accounts, session synchronization, and authentication, you must integrate your Firebase project:

1.  Go to the [Firebase Console](https://console.firebase.google.com/).
2.  Create a new Firebase Project (or select an existing one).
3.  Navigate to **Project Settings > Service Accounts**.
4.  Click **Generate New Private Key**. This downloads a JSON file containing credential information.
5.  Rename the downloaded JSON file to `serviceAccountKey.json`.
6.  Place `serviceAccountKey.json` directly into the root folder of this project (`smart-parking-app/`).
7.  Ensure you have **Email/Password** authentication enabled under the Firebase Authentication tab.


---

## 🏃 Running the Application

1.  Start the Flask development server:
    ```bash
    python app.py
    ```
2.  Open your browser and navigate to:
    ```
    http://127.0.0.1:5000/
    ```

