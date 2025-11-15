# Trucky – FMCSA-Compliant Driver Logbook & Route Planning System

A full-stack logistics and transportation application built with **React (frontend)** and **Django REST Framework (backend)**.  
The system automates **driver logbook generation**, ensures **FMCSA Hours-of-Service (HOS) compliance**, and provides **real-world route planning** using **OSRM (Open Source Routing Machine)**.

This project simulates how US-based trucking companies manage daily logs, duty statuses, and routing—following FMCSA §395 guidelines.

---

## 1. Live Deployment

### Frontend (React + Vercel)
**https://trucky-mu.vercel.app/**

### Backend (Django REST + Render)
**https://trucky.onrender.com**

API Endpoint:
```
POST https://trucky.onrender.com/api/trips/plan/
```

---

## 2. GitHub Repositories

### Frontend Repo
https://github.com/rajib3777/trucky_frontend

### Backend Repo
https://github.com/rajib3777/Trucky

---

## 3. Project Overview

Trucky is an end-to-end logistics solution that allows a driver or dispatcher to:

- Input trip details (current location, pickup, drop-off, cycle hours used)
- Generate a FMCSA-compliant **24-hour driver logbook**
- Calculate duty statuses (Off-Duty, On-Duty, Driving, Sleeper)
- Visualize a real-time route on an interactive map
- Display driving distance, duration, and midpoint rest suggestions
- View a bar-chart summary of duty hours
- Produce recap hours and next-day availability
- Compute total mileage for the day

---

## 4. Key Features

### HOS & Logbook Features
- Automated log grid construction (24-hour FMCSA-compliant)
- Duty status segmentation:
  - Off-Duty
  - On-Duty (Not Driving)
  - Driving
  - Sleeper Berth
- Recap calculation (last 7 days)
- Availability projection for next day
- Total miles driven today
- Real-time distance → driving hours conversion

### Routing Features
- Real-world geocoding via **Nominatim (OpenStreetMap)**
- Real-world routing via **OSRM public API**
- Multi-point polyline for map display
- Dynamic midpoint selection for rest planning
- Accurate duration + distance computation

### Frontend Features
- Fully responsive React interface
- Map visualization using Leaflet
- Graph visualization of HOS totals
- Live API integration
- Real-time UI state updates

### Backend Features
- Django REST Framework
- OSRM route integration
- Modular service architecture:
  - `hos_logic.py`
  - `log_service.py`
  - `map_service.py`
- Clean JSON output matching frontend needs
- Structured CORS-enabled API for external clients

---

## 5. Architecture

```
Frontend (React)
    |
    | POST /api/trips/plan/
    v
Backend (Django + DRF)
│
├── Log Service (HOS + FMCSA Logic)
│       └── hos_logic.py
│
└── Map Service (Nominatim + OSRM)
        ├── _nominatim_geocode()
        ├── _osrm_route()
        └── generate_route_map()
```

---

## 6. API Specification

### Endpoint  
```
POST /api/trips/plan/
```

### Request Body
```json
{
  "currentLocation": "New York, NY",
  "pickupLocation": "Brooklyn, NY",
  "dropoffLocation": "Manhattan, NY",
  "currentCycleUsed": 15
}
```

### Successful Response
The backend returns a **combined logSheet + mapInfo** response:

```json
{
  "logSheet": {
      "grid": [...],
      "totals": {...},
      "recap": {...},
      "driverInfo": {...}
  },
  "mapInfo": {
      "route": [...],
      "stops": [...],
      "mapCenter": [...]
  }
}
```

All JSON fields are dynamically calculated based on real map distance and FMCSA HOS logic.

---

## 7. Technologies Used

### Frontend
- React
- Axios
- Leaflet Maps
- Chart.js
- CSS (Responsive UI)

### Backend
- Django
- Django REST Framework
- OSRM Routing API
- Nominatim Geocoding
- Python 3.12+
- CORS Headers

Deployment:
- Frontend → **Vercel**
- Backend → **Render**

---

## 8. File Structure

### Backend Structure
```
Trucky/
├── trips/
│   ├── services/
│   │   ├── hos_logic.py
│   │   ├── log_service.py
│   │   └── map_service.py
│   ├── views.py
│   ├── serializers.py
│   ├── urls.py
│   ├── models.py
│   └── tests.py
├── trucky/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── .env
```

### Frontend Structure
```
src/
├── components/
│   ├── TripInputForm.js
│   ├── LogSheet.js
│   ├── MapDisplay.js
│   └── ...
├── App.js
├── index.js
└── App.css
```

---

## 9. Local Development Guide

### Clone both repos
```
git clone https://github.com/rajib3777/trucky_frontend
git clone https://github.com/rajib3777/Trucky
```

---

### Backend Setup
```
cd Trucky
python -m venv env
env\Scripts\activate
pip install -r requirements.txt
python manage.py runserver
```

Create `.env`:
```
DEBUG=True
SECRET_KEY=your_secret
MAP_PROVIDER=osrm
ALLOWED_ORIGINS=http://localhost:3000
```

---

### Frontend Setup
```
cd trucky_frontend
npm install
npm start
```

---

## 10. Sample Input–Output for Testing

### Input
```json
{
  "currentLocation": "Chicago, IL",
  "pickupLocation": "Chicago, IL",
  "dropoffLocation": "Detroit, MI",
  "currentCycleUsed": 20
}
```

### Output (Structure)
```
logSheet: {...}
mapInfo: {...}
distance_miles: 280+
duration_hours: 4.5+
```

(Values vary based on OSRM real calculations.)

---

## 11. Deployment Details

### Frontend Deployment
- Vercel build command: `npm run build`
- Output folder: `build/`

### Backend Deployment
- Render blueprint:
  - Runtime: Python
  - Start command: `gunicorn trucky.wsgi:application`
  - Auto deploy from GitHub

CORS enabled:
```
CORS_ALLOW_ALL_ORIGINS = True
```

---

## 12. Author

**Rajibul Islam**  
Full-Stack Developer  
GitHub: https://github.com/rajib3777  
Email: rajibulislam3777@gmail.com  

---

## 13. License

This project is released under the MIT License.

---

# End of Documentation
project submitted by Md.Rajibul Islam SHuvo
Full Stack Developer
Company : Soamdhan Soft
