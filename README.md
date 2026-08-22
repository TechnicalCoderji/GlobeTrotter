# 🌍 GlobeTrotter - AI Multi-City Travel Planner

GlobeTrotter is a full-stack Django travel planning web application built with a **`config`**, **`accounts`**, and **`app`** folder structure. It dynamically queries real AI models (Pollinations AI, OpenRouter, HuggingFace) on-the-fly for **ANY personalized destination** (e.g., *Dwarka, Somnath, Varanasi, Manali, Kedarnath, Goa, Paris, Tokyo...*), formats all budgets & costs in **Indian Rupees (₹)**, and generates non-changeable **username first-letter avatars**.

---

## 🚀 Key Features

1. **Folder Hierarchy Restored**:
   - `config/`: Root settings, WSGI, URLs.
   - `accounts/`: User authentication, registration, login, logout, and profile with dynamic initial-letter avatars.
   - `app/`: Multi-city step-by-step trip planner, dynamic AI place & activity discovery, day-wise relational itinerary builder, budget breakdown in ₹ Rupees, calendar schedule view, JSON export, and community trip cloning.

2. **Personalized Dynamic Destinations (No Static Hardcoding)**:
   - Enter ANY destination or combination of stops (e.g., *Dwarka &rarr; Somnath*).
   - Real-time AI queries fetch authentic local temples, attractions, sightseeing spots, and food options for each specific city.

3. **All Pricing in Indian Rupees (₹)**:
   - Itinerary activity costs, daily budgets, category breakdowns, and AI budget estimates are all calculated and displayed in **₹ INR**.

4. **Dynamic Initial-Letter Avatars**:
   - Avatars are automatically derived from the first letter of the user's username (e.g., **`T`** for `technicalcoderji`, **`A`** for `alex`), with no changeable profile picture upload.

---

## 📦 Folder Structure

```
GlobeTrotter/
├── config/                  # Django project configuration
│   ├── settings.py          # INSTALLED_APPS: accounts, app
│   ├── urls.py              # Root URL router
│   ├── wsgi.py
│   └── asgi.py
├── accounts/                # User Auth & Profile App
│   ├── models.py            # CustomUser (avatar_letter property)
│   ├── forms.py             # RegisterForm, LoginForm, ProfileForm
│   ├── views.py             # register_view, login_view, logout_view, profile_view
│   ├── urls.py              # /auth/login/, /auth/register/, /auth/profile/, etc.
│   └── tests.py
├── app/                     # Core Travel & Itinerary App
│   ├── models.py            # Trip, TripStop, Itinerary, ItineraryItem, City
│   ├── views.py             # home_view, start_trip, step2_events, step3_final_plan, builder, budget, calendar, export, copy
│   ├── ai_helper.py         # Dynamic AI client (search_cities_ai, fetch_activities_for_city_ai, etc.)
│   ├── urls.py              # /start/, /events/, /plan/, /trips/..., /ai/...
│   ├── management/commands/
│   │   └── seed_data.py     # Seeds demo user & personalized Dwarka-Somnath trip in ₹
│   └── tests.py
├── templates/               # Minimal, responsive templates
│   ├── base.html            # Navigation with username initial avatar badge
│   ├── home.html            # Dashboard & resume draft
│   ├── create_step1.html    # Step 1: Multi-city destination picker & dates
│   ├── create_step2.html    # Step 2: Live AI activity selection
│   ├── auth/                # login.html, register.html, profile.html
│   ├── trips/               # itinerary_builder.html, budget.html, calendar.html, trip_list.html, etc.
│   └── ai_services/         # ai_tools.html (Interactive AI Travel Lab)
└── static/css/style.css     # Clean modern CSS
```

---

## ⚡ Quick Start

```bash
# 1. Apply database migrations
python manage.py migrate

# 2. Seed initial demo data
python manage.py seed_data

# 3. Start development server
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

### 🔑 Demo Account
- **Username:** `technicalcoderji`
- **Password:** `Coderji123!`

---

## 🧪 Run Automated Tests
```bash
python manage.py test
```
All 13 unit tests pass across authentication, initial-letter avatars, multi-city planning flow, dynamic activity insertion, budget calculations in ₹ INR, calendar schedule views, JSON export, and AI REST endpoints.
