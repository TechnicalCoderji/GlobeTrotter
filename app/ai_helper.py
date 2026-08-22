import os
import json
import re
import urllib.parse
import requests
from django.conf import settings

OPENROUTER_API_KEY = getattr(settings, 'OPENROUTER_API_KEY', os.getenv('OPENROUTER_API_KEY', ''))
HUGGINGFACE_API_KEY = getattr(settings, 'HUGGINGFACE_API_KEY', os.getenv('HUGGINGFACE_API_KEY', ''))

def clean_json_response(raw_text):
    """Clean markdown code blocks and extract valid JSON."""
    if not raw_text:
        return None
    match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', raw_text)
    if match:
        raw_text = match.group(1)
    try:
        return json.loads(raw_text.strip())
    except Exception:
        start = raw_text.find('{')
        end = raw_text.rfind('}')
        if start != -1 and end != -1:
            try:
                return json.loads(raw_text[start:end+1])
            except Exception:
                pass
        # Try array
        start_arr = raw_text.find('[')
        end_arr = raw_text.rfind(']')
        if start_arr != -1 and end_arr != -1:
            try:
                return json.loads(raw_text[start_arr:end_arr+1])
            except Exception:
                pass
    return None


def call_ai_text(prompt, system_prompt=None):
    """
    Calls OpenRouter / HuggingFace or Pollinations AI dynamic endpoint.
    """
    # 1. OpenRouter
    if OPENROUTER_API_KEY:
        try:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "GlobeTrotter",
            }
            payload = {
                "model": "mistralai/mistral-7b-instruct:free",
                "messages": [
                    {"role": "system", "content": system_prompt or "You are a professional travel planner. Return clean text or JSON as requested."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
            }
            resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                return data['choices'][0]['message']['content']
        except Exception as e:
            print(f"[AI Helper] OpenRouter error: {e}")

    # 2. HuggingFace
    if HUGGINGFACE_API_KEY:
        try:
            headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
            payload = {"inputs": prompt, "parameters": {"max_new_tokens": 1000, "return_full_text": False}}
            resp = requests.post("https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2", headers=headers, json=payload, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0 and 'generated_text' in data[0]:
                    return data[0]['generated_text']
        except Exception as e:
            print(f"[AI Helper] HuggingFace error: {e}")

    # 3. Pollinations AI Free Endpoint
    try:
        full = f"{system_prompt or ''}\n\n{prompt}"
        encoded = urllib.parse.quote(full)
        resp = requests.get(f"https://text.pollinations.ai/{encoded}", timeout=6)
        if resp.status_code == 200 and resp.text:
            return resp.text
    except Exception as e:
        print(f"[AI Helper] Pollinations error: {e}")

    return None


# -------------------------------------------------------------------------
# 1. DYNAMIC CITY SEARCH WITH AI
# -------------------------------------------------------------------------
def search_cities_ai(query):
    """
    Dynamically generates and returns real travel destinations matching query.
    e.g. for "Dwarka" -> ["Dwarka, Gujarat", "Bet Dwarka, Gujarat", "Somnath, Gujarat"]
    """
    if not query:
        return []

    prompt = (
        f"Return a list of up to 5 real travel destinations and cities matching '{query}' in English. "
        f"Format each as 'City, State/Country'. Separate each result with a pipe character '|'. "
        f"Do not use numbered lists or intro text."
    )
    raw = call_ai_text(prompt, "You are a global geographical database.")
    if raw:
        results = [c.strip() for c in raw.split('|') if c.strip() and len(c) < 70 and not c.startswith('Here')]
        if results:
            return results

    # Fallback search matching
    q_lower = query.lower()
    famous_places = [
        "Dwarka, Gujarat", "Somnath, Gujarat", "Gir National Park, Gujarat", "Statue of Unity, Gujarat",
        "Varanasi, Uttar Pradesh", "Ayodhya, Uttar Pradesh", "Agra, Uttar Pradesh",
        "Jaipur, Rajasthan", "Udaipur, Rajasthan", "Jodhpur, Rajasthan", "Jaisalmer, Rajasthan",
        "Manali, Himachal Pradesh", "Shimla, Himachal Pradesh", "Dharamshala, Himachal Pradesh",
        "Rishikesh, Uttarakhand", "Haridwar, Uttarakhand", "Kedarnath, Uttarakhand",
        "Goa, India", "Munnar, Kerala", "Alleppey, Kerala", "Ooty, Tamil Nadu",
        "Amritsar, Punjab", "Leh Ladakh, India", "Kashmir, India", "Darjeeling, West Bengal",
        "Paris, France", "Tokyo, Japan", "Rome, Italy", "Dubai, UAE", "London, UK"
    ]
    matched = [p for p in famous_places if q_lower in p.lower()]
    if not matched:
        matched = [f"{query.title()}, India"]
    return matched[:5]


# -------------------------------------------------------------------------
# 2. DYNAMIC ACTIVITIES & PLACES FETCHING WITH AI (IN RUPEES ₹)
# -------------------------------------------------------------------------
def fetch_activities_for_city_ai(city_name):
    """
    Dynamically queries AI for real places, temples, food, sightseeing in {city_name} with costs in ₹ INR.
    """
    prompt = (
        f"List 6 popular and real tourist attractions, temples, sightseeing spots, and activities in {city_name}.\n"
        "Return ONLY a JSON array of objects with this schema:\n"
        "[\n"
        '  {\n'
        '    "name": "Dwarkadhish Temple Darshan",\n'
        '    "category": "culture",\n'
        '    "estimated_cost": 200,\n'
        '    "duration": "2 hours",\n'
        '    "description": "Sacred temple dedicated to Lord Krishna along Gomti river."\n'
        '  }\n'
        ']\n'
        "Valid categories: sightseeing, food, adventure, culture, relaxation.\n"
        "All estimated costs MUST be in Indian Rupees (₹ INR)."
    )

    raw = call_ai_text(prompt, "You are a local tour guide in India and worldwide. Always output valid JSON array with costs in Indian Rupees (₹).")
    if raw:
        parsed = clean_json_response(raw)
        if isinstance(parsed, list) and len(parsed) > 0:
            return parsed
        elif isinstance(parsed, dict) and 'activities' in parsed:
            return parsed['activities']

    # Dynamic fallback based on city name
    city_clean = city_name.split(',')[0].strip()
    city_lower = city_clean.lower()

    if 'dwarka' in city_lower:
        return [
            {"name": "Dwarkadhish Temple (Jagat Mandir) Darshan", "category": "culture", "estimated_cost": 150, "duration": "2.5 hours", "description": "Ancient 5-story temple dedicated to Lord Krishna with divine Aarti."},
            {"name": "Bet Dwarka Island & Ferry Boat Ride", "category": "adventure", "estimated_cost": 300, "duration": "3.5 hours", "description": "Ferry ride across the Gulf of Kutch to the historic island residence of Krishna."},
            {"name": "Nageshwar Jyotirlinga Temple Visit", "category": "culture", "estimated_cost": 100, "duration": "1.5 hours", "description": "One of the 12 sacred Jyotirlinga shrines with giant Shiva statue."},
            {"name": "Rukmini Devi Temple Darshan", "category": "culture", "estimated_cost": 80, "duration": "1 hour", "description": "Intricately carved 12th-century architectural heritage temple."},
            {"name": "Shivrajpur Blue Flag Beach & Water Sports", "category": "relaxation", "estimated_cost": 450, "duration": "3 hours", "description": "Pristine white sand certified Blue Flag beach with sunset views."},
            {"name": "Gomti Ghat Walk & Evening Aarti", "category": "sightseeing", "estimated_cost": 50, "duration": "1.5 hours", "description": "Peaceful evening stroll where Gomti river meets the Arabian Sea."},
            {"name": "Authentic Gujarati Thali Dinner", "category": "food", "estimated_cost": 250, "duration": "1 hour", "description": "Unlimited authentic kathiyawadi & gujarati thali with farsan and sweets."}
        ]
    elif 'somnath' in city_lower:
        return [
            {"name": "Somnath Temple Darshan (First Jyotirlinga)", "category": "culture", "estimated_cost": 150, "duration": "2.5 hours", "description": "Majestic seaside temple honoring the first of twelve Jyotirlingas."},
            {"name": "Somnath Light & Sound Show at Sea Promenade", "category": "sightseeing", "estimated_cost": 100, "duration": "1 hour", "description": "Evening laser narrative on the history of the temple with sea breeze."},
            {"name": "Bhalka Tirth & Dehotsarg Teerth", "category": "culture", "estimated_cost": 80, "duration": "1.5 hours", "description": "Sacred pilgrimage spot where Lord Krishna concluded his earthly avatar."},
            {"name": "Triveni Sangam Holy Dip & Boat Ride", "category": "adventure", "estimated_cost": 200, "duration": "1.5 hours", "description": "Confluence of three sacred rivers: Hiran, Kapila, and Saraswati."},
            {"name": "Somnath Beach Sunset Walk & Coconut Water", "category": "relaxation", "estimated_cost": 60, "duration": "1.5 hours", "description": "Waves crashing along the temple perimeter beach."},
            {"name": "Prabhas Patan Museum Artifacts", "category": "culture", "estimated_cost": 50, "duration": "1 hour", "description": "Ancient sculptures and stone remains of original temple architecture."}
        ]
    elif 'varanasi' in city_lower:
        return [
            {"name": "Kashi Vishwanath Temple Corridor Darshan", "category": "culture", "estimated_cost": 250, "duration": "2.5 hours", "description": "Historic golden temple dedicated to Lord Shiva in heart of Banaras."},
            {"name": "Sunrise Ganga River Boat Ride at Assi Ghat", "category": "adventure", "estimated_cost": 350, "duration": "2 hours", "description": "Rowboat cruise gliding past ancient bathing ghats and historic palaces."},
            {"name": "Grand Evening Ganga Aarti at Dashashwamedh Ghat", "category": "sightseeing", "estimated_cost": 100, "duration": "1.5 hours", "description": "Hypnotic synchronized ritual with fire lamps, bells, and incense."},
            {"name": "Sarnath Buddhist Monuments & Deer Park", "category": "culture", "estimated_cost": 150, "duration": "3 hours", "description": "Where Buddha gave his first sermon; see Dhamek Stupa & Ashoka Pillar."},
            {"name": "Banarasi Street Food & Kachori Jalebi Trail", "category": "food", "estimated_cost": 200, "duration": "1.5 hours", "description": "Famous Malaiyo, Tamatar Chaat, Blue Lassi, and Banarasi Paan."},
            {"name": "Silk Weaving Heritage Alleys Walking Tour", "category": "culture", "estimated_cost": 100, "duration": "2 hours", "description": "Watch master weavers create authentic Banarasi silk sarees."}
        ]
    else:
        return [
            {"name": f"Iconic Landmarks & Heritage Walk in {city_clean}", "category": "sightseeing", "estimated_cost": 200, "duration": "2.5 hours", "description": f"Explore historic monuments, architecture, and central squares of {city_clean}."},
            {"name": f"Authentic Regional Food & Street Delicacies in {city_clean}", "category": "food", "estimated_cost": 300, "duration": "1.5 hours", "description": f"Taste famous regional dishes, snacks, and traditional desserts in {city_clean}."},
            {"name": f"Main Temple / Cultural Heritage Center of {city_clean}", "category": "culture", "estimated_cost": 150, "duration": "2 hours", "description": "Discover centuries of heritage, architecture, and spiritual traditions."},
            {"name": f"Scenic Nature Spot & Sunset Viewpoint in {city_clean}", "category": "adventure", "estimated_cost": 250, "duration": "2 hours", "description": "Panoramic vantage points offering golden-hour views and photography."},
            {"name": f"Local Artisan & Handicraft Bazaar Shopping", "category": "culture", "estimated_cost": 200, "duration": "2 hours", "description": "Browse handmade souvenirs, textiles, and authentic regional crafts."},
            {"name": f"Evening Garden Walk & Cafe Relaxation in {city_clean}", "category": "relaxation", "estimated_cost": 150, "duration": "1.5 hours", "description": "Relax in serene landscaped botanical gardens with refreshments."}
        ]


# -------------------------------------------------------------------------
# 3. DYNAMIC ITINERARY GENERATOR (ALL IN ₹ RUPEES)
# -------------------------------------------------------------------------
def generate_ai_itinerary_rupees(destination, days=3, budget_inr=15000):
    """
    Generates a structured day-wise travel plan in Indian Rupees (₹).
    """
    days = max(1, min(int(days), 14))
    budget_inr = max(1000, float(budget_inr))

    prompt = (
        f"Generate a detailed day-wise travel itinerary for {destination} for {days} days under ₹{budget_inr} INR budget.\n"
        "Return ONLY a JSON object with this exact structure:\n"
        "{\n"
        f'  "destination": "{destination}",\n'
        f'  "days_count": {days},\n'
        f'  "total_budget": {budget_inr},\n'
        '  "currency": "INR",\n'
        '  "days": [\n'
        '    {\n'
        '      "day": 1,\n'
        '      "theme": "Arrival & Sacred Darshan",\n'
        '      "city_name": "Main City",\n'
        '      "notes": "Morning start at 08:00 AM",\n'
        '      "activities": [\n'
        '        {\n'
        '          "time": "08:30 AM",\n'
        '          "activity_name": "Historic Temple Visit",\n'
        '          "category": "culture",\n'
        '          "estimated_cost": 200,\n'
        '          "duration": "2.5 hours",\n'
        '          "description": "Darshan and architectural exploration."\n'
        '        }\n'
        '      ]\n'
        '    }\n'
        '  ]\n'
        '}'
    )

    raw = call_ai_text(prompt, "You are an expert travel planner for India and global destinations. Always return valid JSON with costs in Indian Rupees (₹).")
    if raw:
        parsed = clean_json_response(raw)
        if parsed and 'days' in parsed and isinstance(parsed['days'], list) and len(parsed['days']) > 0:
            return parsed

    # Dynamic Fallback in INR
    daily_budget = round(budget_inr / days, 2)
    sample_acts = fetch_activities_for_city_ai(destination)

    days_list = []
    times = ["08:30 AM", "01:00 PM", "04:30 PM", "07:30 PM"]

    for d in range(1, days + 1):
        day_acts = []
        # pick 3 activities per day
        start_idx = ((d - 1) * 3) % len(sample_acts)
        for i in range(3):
            act = sample_acts[(start_idx + i) % len(sample_acts)]
            day_acts.append({
                "time": times[i % len(times)],
                "activity_name": act.get("name", "Local Exploration"),
                "category": act.get("category", "sightseeing"),
                "estimated_cost": act.get("estimated_cost", 200),
                "duration": act.get("duration", "2 hours"),
                "description": act.get("description", "")
            })

        days_list.append({
            "day": d,
            "theme": f"Day {d}: {destination} Highlights",
            "city_name": destination.split(',')[0].strip(),
            "notes": "Comfortable footwear and camera recommended.",
            "allocated_budget": daily_budget,
            "activities": day_acts
        })

    return {
        "destination": destination,
        "days_count": days,
        "total_budget": budget_inr,
        "currency": "INR",
        "source": "GlobeTrotter Dynamic AI",
        "days": days_list
    }


# -------------------------------------------------------------------------
# 4. DYNAMIC SMART BUDGET IN RUPEES (₹)
# -------------------------------------------------------------------------
def generate_smart_budget_rupees(destination, days=3):
    """
    Estimates realistic travel budget breakdown in Indian Rupees (₹).
    """
    days = max(1, int(days))

    prompt = (
        f"Estimate the travel budget for a trip to {destination} for {days} days for a traveler in Indian Rupees (INR).\n"
        "Return ONLY a JSON object with this exact structure:\n"
        "{\n"
        f'  "destination": "{destination}",\n'
        f'  "days": {days},\n'
        '  "currency": "INR",\n'
        '  "tier": "Moderate",\n'
        '  "estimated_total_budget": 12000,\n'
        '  "daily_average": 3000,\n'
        '  "breakdown": {\n'
        '    "accommodation": 5500,\n'
        '    "food_and_dining": 3000,\n'
        '    "activities_and_tours": 1800,\n'
        '    "local_transport": 1200,\n'
        '    "miscellaneous": 500\n'
        '  },\n'
        '  "cost_saving_tips": [\n'
        '    "Book dharamshala or guest houses near main temple",\n'
        '    "Use shared autos or local state transport buses"\n'
        '  ]\n'
        '}'
    )

    raw = call_ai_text(prompt, "You are a travel budgeting specialist in India and abroad. Output strictly valid JSON in INR.")
    if raw:
        parsed = clean_json_response(raw)
        if parsed and 'breakdown' in parsed and 'estimated_total_budget' in parsed:
            return parsed

    # Dynamic calculation based on days
    daily_base = 3200
    total = daily_base * days
    return {
        "destination": destination,
        "days": days,
        "currency": "INR",
        "tier": "Moderate Travel Tier",
        "estimated_total_budget": total,
        "daily_average": daily_base,
        "breakdown": {
            "accommodation": round(total * 0.45, 2),
            "food_and_dining": round(total * 0.25, 2),
            "activities_and_tours": round(total * 0.18, 2),
            "local_transport": round(total * 0.08, 2),
            "miscellaneous": round(total * 0.04, 2)
        },
        "cost_saving_tips": [
            f"Pre-book temple special darshan tickets online to save waiting time in {destination}.",
            "Use shared autos or local transport for inter-city hops (e.g. Dwarka to Somnath).",
            "Try authentic local dining halls (bhojanalayas) for fresh, affordable meals."
        ],
        "source": "GlobeTrotter Budget Engine (INR)"
    }
