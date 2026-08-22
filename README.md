# 🌍 GlobeTrotter

### Empowering Personalized Travel Planning

GlobeTrotter is a full-stack travel planning platform developed for the Odoo Hackathon. It helps users create personalized multi-city trips, organize destinations and activities, manage itineraries, estimate budgets, visualize travel plans, and share trips.

## 🚀 Project Overview

Planning a multi-city trip often requires managing destinations, dates, activities, expenses, and itineraries across multiple platforms. GlobeTrotter brings these tasks together into one connected travel-planning experience.

### Main Goals

- Create customized multi-city itineraries
- Manage travel dates and destinations
- Discover activities and places
- Organize day-wise itineraries
- Estimate and track trip expenses
- View trips through timeline/calendar views
- Share travel plans with others
- Provide a clean and responsive travel-focused interface

## ✨ Key Features

### 🔐 Authentication
- User registration
- User login
- Logout
- User-specific travel data

### 🧳 Trip Management
- Create trips
- Add travel dates
- Manage multiple destinations/stops
- View existing trips
- Edit and delete trips

### 📍 Destination Discovery
- Search destinations
- Explore cities
- Add destinations to trips
- View destination information

### 🎯 Activity Planning
- Discover activities
- Add activities to a trip
- Organize activities around destinations and dates

### 🗓️ Itinerary Builder
- Build multi-city itineraries
- Organize travel stops
- View day-wise plans
- Manage activities within the itinerary

### 💰 Budget & Cost Planning
- Estimate total trip cost
- Track activity and other expenses
- View budget breakdown
- Calculate approximate daily spending

### 📅 Calendar / Timeline
- Visualize trip dates
- View itinerary by day
- Understand the complete journey flow

### 🤝 Community & Sharing
- Explore public/shared trips
- Share travel plans
- View shared itineraries
- Copy trips where supported

## 🎨 UI / Design

The interface follows a modern travel-dashboard design inspired by the GlobeTrotter concept.

- Light travel-themed background
- White rounded content cards
- Blue/teal accents
- Large travel imagery
- Dashboard layout
- Sidebar navigation
- Trip and itinerary cards
- Budget and activity panels
- Responsive layout

## 🛠️ Technology Stack

### Frontend
- HTML5
- CSS3
- JavaScript
- Fetch API

### Backend
- Python
- Django
- Django REST Framework where applicable

### Database
- Relational database
- SQLite for local development where configured

## 🏗️ Architecture

```text
Frontend (HTML/CSS/JavaScript)
              │
              │ Fetch / API
              ▼
       Django Backend
              │
              ▼
      Relational Database
```

## 👥 Team

| Member | Role | Responsibility |
|---|---|---|
| **Dip** | Team Leader + Backend Developer | Django backend, database, APIs and backend logic |
| **Hardik** | Frontend Developer | HTML, CSS, JavaScript and user interface |
| **Aman** | Integration Developer | Frontend-backend integration, API communication, data flow and testing |

## 🔄 Integration Flow

```text
User Action
    ↓
Frontend
    ↓
Fetch API
    ↓
Django API
    ↓
Backend Processing
    ↓
Database
    ↓
JSON Response
    ↓
Frontend UI Update
```

For example, when a user creates a trip:

```text
Create Trip Form
      ↓
JavaScript Request
      ↓
Django API
      ↓
Database
      ↓
Success Response
      ↓
Trip Appears in Dashboard
```

## 📁 Suggested Project Structure

```text
GlobeTrotter/
├── frontend/
│   ├── index.html
│   ├── login.html
│   ├── signup.html
│   ├── dashboard.html
│   ├── create-trip.html
│   ├── my-trips.html
│   ├── itinerary.html
│   ├── city-search.html
│   ├── activity-search.html
│   ├── budget.html
│   ├── calendar.html
│   ├── shared-trip.html
│   ├── profile.html
│   ├── css/
│   ├── js/
│   └── assets/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── config/
│   ├── accounts/
│   ├── trips/
│   ├── destinations/
│   ├── activities/
│   └── budgets/
├── README.md
└── .gitignore
```

> Adjust the structure above to match the actual files in the final repository.

## 💻 Running the Backend on Windows

Open Command Prompt or PowerShell in the backend directory.

### 1. Create virtual environment

```bash
python -m venv venv
```

### 2. Activate it

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply migrations

```bash
python manage.py migrate
```

### 5. Create an admin user if required

```bash
python manage.py createsuperuser
```

### 6. Start Django

```bash
python manage.py runserver
```

The Django development server will normally be available at `http://127.0.0.1:8000/`.

## 🌐 Running the Frontend

Run the frontend using the method configured for the project. If the frontend uses local HTML files, open the appropriate entry page. For development, VS Code Live Server can be used if configured.

Make sure the frontend API base URL matches the running Django backend.

## 🔌 API Integration

Typical operations include:

```text
POST   /api/auth/register/
POST   /api/auth/login/
GET    /api/trips/
POST   /api/trips/
GET    /api/trips/<id>/
PUT    /api/trips/<id>/
DELETE /api/trips/<id>/
GET    /api/cities/
GET    /api/activities/
POST   /api/trips/<id>/stops/
POST   /api/trips/<id>/activities/
GET    /api/trips/<id>/budget/
GET    /api/trips/<id>/calendar/
POST   /api/trips/<id>/share/
```

> Endpoint names may differ in the final implementation. Refer to the Django URL configuration for the exact routes.

## 🧪 Testing Checklist

- [ ] Registration works
- [ ] Login works
- [ ] Logout works
- [ ] Dashboard loads
- [ ] Trips can be created
- [ ] Trips can be viewed
- [ ] Trips can be edited
- [ ] Trips can be deleted
- [ ] Destinations can be searched
- [ ] Activities can be added
- [ ] Itinerary data is saved
- [ ] Budget calculations work
- [ ] Calendar/timeline works
- [ ] Sharing works where implemented
- [ ] Frontend communicates with backend
- [ ] Database stores and retrieves data
- [ ] No major browser console errors
- [ ] No broken buttons or pages

## 🌱 Future Scope

- Live maps and route planning
- Flight and hotel integrations
- Real-time travel pricing
- Advanced AI itinerary generation
- Weather-based planning
- Personalized recommendations
- Collaborative trip editing
- Mobile application
- Notifications and reminders
- Advanced analytics

## 🏆 Hackathon Focus

The core travel-planning journey is:

```text
Discover
   ↓
Create Trip
   ↓
Add Destinations
   ↓
Add Activities
   ↓
Build Itinerary
   ↓
Manage Budget
   ↓
View Timeline
   ↓
Share Trip
```

## 📜 Problem Statement Alignment

GlobeTrotter is designed around the Odoo hackathon requirement for personalized multi-city travel planning with destinations, activities, budgets, itinerary visualization, sharing, a responsive interface, and relational travel data management.

## 👨‍💻 Team Contribution

### Dip — Team Leader / Backend
- Django backend
- Database design
- API development
- Authentication
- Backend business logic

### Hardik — Frontend
- UI/UX implementation
- HTML
- CSS
- JavaScript
- Responsive design
- User interaction

### Aman — Integration
- Frontend and backend connection
- API integration
- Data flow
- Authentication integration
- Error handling
- End-to-end testing

## 📌 Important Note

This README describes the intended GlobeTrotter architecture and functionality. Features should only be presented as completed when they are actually implemented and tested in the final build.

---

# 🌍 GlobeTrotter

### Plan Smarter. Travel Better.
