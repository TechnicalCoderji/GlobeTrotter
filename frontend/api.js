/**
 * GlobeTrotter API Client
 * Seamlessly connects the static/dynamic frontend to the Django backend APIs.
 * Preserves backend contracts, handles session auth, CSRF, and AI endpoints.
 */

const API_BASE = (window.location.origin && window.location.origin.includes(':8000')) ? '' : 'http://127.0.0.1:8000';

// Utility to get CSRF token from cookie
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Global Toast Notification Helper
function showToast(message, type = 'info') {
  let toastContainer = document.getElementById('gt-toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'gt-toast-container';
    toastContainer.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 99999;
      display: flex;
      flex-direction: column;
      gap: 10px;
      max-width: 380px;
      pointer-events: none;
    `;
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement('div');
  const bgColors = {
    success: '#10b981',
    error: '#ef4444',
    warning: '#f59e0b',
    info: '#0284c7'
  };
  const icons = {
    success: 'fa-circle-check',
    error: 'fa-circle-exclamation',
    warning: 'fa-triangle-exclamation',
    info: 'fa-circle-info'
  };

  toast.style.cssText = `
    background: #ffffff;
    color: #1e293b;
    padding: 12px 18px;
    border-radius: 10px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.15);
    border-left: 5px solid ${bgColors[type] || bgColors.info};
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 0.9rem;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 500;
    pointer-events: auto;
    animation: gtSlideIn 0.3s ease forwards;
    transition: opacity 0.3s ease, transform 0.3s ease;
  `;

  toast.innerHTML = `
    <i class="fa-solid ${icons[type] || icons.info}" style="color: ${bgColors[type] || bgColors.info}; font-size: 1.15rem;"></i>
    <div style="flex: 1; line-height: 1.4;">${message}</div>
    <button style="background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 0.85rem;" onclick="this.parentElement.remove()">✕</button>
  `;

  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(-10px)';
    setTimeout(() => toast.remove(), 300);
  }, 4500);
}

// Button loading state helper
function setButtonLoading(btn, isLoading, loadingText = 'Please wait...') {
  if (!btn) return;
  if (isLoading) {
    btn.dataset.origText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> ${loadingText}`;
    btn.style.opacity = '0.75';
    btn.style.cursor = 'not-allowed';
  } else {
    btn.disabled = false;
    btn.innerHTML = btn.dataset.origText || 'Submit';
    btn.style.opacity = '1';
    btn.style.cursor = 'pointer';
  }
}

// Local storage user cache for snappy UI
const GT_STORAGE_KEY = 'globetrotter_active_user';
const GT_TRIP_KEY = 'globetrotter_active_trip';

const GlobeTrotterAPI = {
  // ----------------------------------------------------
  // AUTHENTICATION
  // ----------------------------------------------------
  async login(username, password) {
    const csrfToken = getCookie('csrftoken') || '';
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    if (csrfToken) formData.append('csrfmiddlewaretoken', csrfToken);

    try {
      const response = await fetch(`${API_BASE}/auth/login/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': csrfToken,
        },
        body: formData.toString(),
        credentials: 'include'
      });

      if (response.ok || response.redirected) {
        const userObj = {
          username: username,
          first_name: username.charAt(0).toUpperCase() + username.slice(1),
          avatar_letter: username.charAt(0).toUpperCase()
        };
        localStorage.setItem(GT_STORAGE_KEY, JSON.stringify(userObj));
        return { success: true, user: userObj };
      } else {
        const text = await response.text();
        return { success: false, error: 'Invalid username or password. Please check your credentials.' };
      }
    } catch (err) {
      console.error('Login error:', err);
      return { success: false, error: 'Network error communicating with authentication server.' };
    }
  },

  async register(userData) {
    const csrfToken = getCookie('csrftoken') || '';
    const formData = new URLSearchParams();
    for (const key in userData) {
      formData.append(key, userData[key]);
    }
    if (csrfToken) formData.append('csrfmiddlewaretoken', csrfToken);

    try {
      const response = await fetch(`${API_BASE}/auth/register/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': csrfToken,
        },
        body: formData.toString(),
        credentials: 'include'
      });

      if (response.ok || response.redirected) {
        const userObj = {
          username: userData.username,
          first_name: userData.first_name || userData.username,
          last_name: userData.last_name || '',
          email: userData.email,
          city: userData.city || '',
          country: userData.country || '',
          bio: userData.bio || '',
          avatar_letter: (userData.first_name || userData.username).charAt(0).toUpperCase()
        };
        localStorage.setItem(GT_STORAGE_KEY, JSON.stringify(userObj));
        return { success: true, user: userObj };
      } else {
        const text = await response.text();
        return { success: false, error: 'Registration failed. The username or email might already be registered.' };
      }
    } catch (err) {
      console.error('Registration error:', err);
      return { success: false, error: 'Network error communicating with server.' };
    }
  },

  async logout() {
    try {
      localStorage.removeItem(GT_STORAGE_KEY);
      localStorage.removeItem(GT_TRIP_KEY);
      await fetch(`${API_BASE}/auth/logout/`, {
        method: 'GET',
        credentials: 'include'
      });
    } catch (e) {
      console.warn('Logout network notice:', e);
    }
    window.location.href = 'login.html';
  },

  getActiveUser() {
    const stored = localStorage.getItem(GT_STORAGE_KEY);
    if (stored) {
      try {
        return JSON.parse(stored);
      } catch (e) {
        return null;
      }
    }
    return {
      username: 'technicalcoderji',
      first_name: 'Technical',
      last_name: 'Coderji',
      email: 'coderji@globetrotter.io',
      city: 'Ahmedabad',
      country: 'India',
      bio: 'Passionate traveler, spiritual explorer, and developer.',
      avatar_letter: 'T'
    };
  },

  setActiveUser(user) {
    localStorage.setItem(GT_STORAGE_KEY, JSON.stringify(user));
  },

  // ----------------------------------------------------
  // AI & DISCOVERY ENDPOINTS
  // ----------------------------------------------------
  async searchCities(query) {
    if (!query) return [];
    try {
      const resp = await fetch(`${API_BASE}/cities/search/?q=${encodeURIComponent(query)}&format=json`);
      if (resp.ok) {
        const data = await resp.json();
        return data.cities || [];
      }
    } catch (err) {
      console.warn('City search fallback:', err);
    }
    const defaults = [
      { name: "Dwarka", country: "Gujarat, India", full: "Dwarka, Gujarat, India" },
      { name: "Somnath", country: "Gujarat, India", full: "Somnath, Gujarat, India" },
      { name: "Varanasi", country: "Uttar Pradesh, India", full: "Varanasi, UP, India" },
      { name: "Manali", country: "Himachal Pradesh, India", full: "Manali, HP, India" },
      { name: "Goa", country: "India", full: "Goa, India" },
      { name: "Ayodhya", country: "Uttar Pradesh, India", full: "Ayodhya, UP, India" },
      { name: "Paris", country: "France", full: "Paris, France" },
      { name: "Rome", country: "Italy", full: "Rome, Italy" },
      { name: "Tokyo", country: "Japan", full: "Tokyo, Japan" }
    ];
    return defaults.filter(d => d.name.toLowerCase().includes(query.toLowerCase()));
  },

  async fetchActivitiesForCity(cityName) {
    if (!cityName) return [];
    try {
      const resp = await fetch(`${API_BASE}/ai/activities/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ city: cityName })
      });
      if (resp.ok) {
        const data = await resp.json();
        if (data.activities && Array.isArray(data.activities)) {
          return data.activities;
        }
      }
    } catch (err) {
      console.warn('Activities AI fetch notice:', err);
    }

    const cityClean = cityName.split(',')[0].trim().toLowerCase();
    if (cityClean.includes('dwarka')) {
      return [
        {
          name: "Dwarkadhish Temple (Jagat Mandir) Darshan",
          category: "culture",
          estimated_cost: 150,
          duration: "2.5 hours",
          description: "Ancient 5-story sacred temple dedicated to Lord Krishna with divine Mangla Aarti.",
          image_url: "https://images.unsplash.com/photo-1609766857041-ed402ea8069a?auto=format&fit=crop&w=400&q=80"
        },
        {
          name: "Bet Dwarka Island & Ferry Boat Ride",
          category: "adventure",
          estimated_cost: 300,
          duration: "3.5 hours",
          description: "Scenic ferry ride across the Gulf of Kutch to the historic island residence of Lord Krishna.",
          image_url: "https://images.unsplash.com/photo-1544644181-1484b3fdfc62?auto=format&fit=crop&w=400&q=80"
        },
        {
          name: "Nageshwar Jyotirlinga Temple Visit",
          category: "culture",
          estimated_cost: 100,
          duration: "1.5 hours",
          description: "One of the 12 sacred Jyotirlinga shrines featuring a towering Shiva statue.",
          image_url: "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&w=400&q=80"
        },
        {
          name: "Shivrajpur Blue Flag Beach & Water Sports",
          category: "relaxation",
          estimated_cost: 450,
          duration: "3 hours",
          description: "Pristine certified Blue Flag white sand beach with breathtaking Arabian Sea sunset views.",
          image_url: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=400&q=80"
        },
        {
          name: "Gomti Ghat Walk & Evening Aarti",
          category: "sightseeing",
          estimated_cost: 50,
          duration: "1.5 hours",
          description: "Peaceful riverbank promenade where Gomti River meets the Arabian Sea.",
          image_url: "https://images.unsplash.com/photo-1518684079-3c830dcef090?auto=format&fit=crop&w=400&q=80"
        },
        {
          name: "Authentic Gujarati Thali Lunch & Farsan",
          category: "food",
          estimated_cost: 250,
          duration: "1 hour",
          description: "Traditional unlimited Kathiyawadi dining with fresh rotla, khichdi, and sweet delicacies.",
          image_url: "https://images.unsplash.com/photo-1613292443284-8d10ef9383fe?auto=format&fit=crop&w=400&q=80"
        }
      ];
    } else if (cityClean.includes('somnath')) {
      return [
        {
          name: "Somnath Temple Darshan (First Jyotirlinga)",
          category: "culture",
          estimated_cost: 150,
          duration: "2.5 hours",
          description: "Majestic seaside temple honoring the first of twelve Jyotirlingas of Lord Shiva.",
          image_url: "https://images.unsplash.com/photo-1609766857041-ed402ea8069a?auto=format&fit=crop&w=400&q=80"
        },
        {
          name: "Somnath Light & Sound Show at Sea Promenade",
          category: "sightseeing",
          estimated_cost: 100,
          duration: "1 hour",
          description: "Evening laser and audio narrative on the history of the temple with sea breeze.",
          image_url: "https://images.unsplash.com/photo-1516483638261-f4dbaf036963?auto=format&fit=crop&w=400&q=80"
        },
        {
          name: "Triveni Sangam Holy Dip & Boat Ride",
          category: "adventure",
          estimated_cost: 200,
          duration: "1.5 hours",
          description: "Confluence of three sacred rivers: Hiran, Kapila, and Saraswati.",
          image_url: "https://images.unsplash.com/photo-1544644181-1484b3fdfc62?auto=format&fit=crop&w=400&q=80"
        },
        {
          name: "Bhalka Tirth Sacred Visit",
          category: "culture",
          estimated_cost: 80,
          duration: "1 hour",
          description: "Sacred pilgrimage site where Lord Krishna concluded his earthly avatar.",
          image_url: "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&w=400&q=80"
        },
        {
          name: "Somnath Beach Sunset Walk & Fresh Coconut Water",
          category: "relaxation",
          estimated_cost: 60,
          duration: "1.5 hours",
          description: "Stroll along the temple perimeter beach enjoying golden hour ocean waves.",
          image_url: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=400&q=80"
        },
        {
          name: "Prabhas Patan Museum & Historical Relics",
          category: "culture",
          estimated_cost: 50,
          duration: "1 hour",
          description: "Ancient stone sculptures and preserved artifacts of original temple eras.",
          image_url: "https://images.unsplash.com/photo-1565099824688-e93eb20fe527?auto=format&fit=crop&w=400&q=80"
        }
      ];
    } else {
      return [
        {
          name: `Historic Landmark & Heritage Tour in ${cityName.split(',')[0]}`,
          category: "sightseeing",
          estimated_cost: 250,
          duration: "2.5 hours",
          description: `Explore the premier cultural and architectural landmarks in ${cityName}.`,
          image_url: "https://images.unsplash.com/photo-1511739001486-6bfe10ce785f?auto=format&fit=crop&w=400&q=80"
        },
        {
          name: `Authentic Regional Cuisine & Dining in ${cityName.split(',')[0]}`,
          category: "food",
          estimated_cost: 350,
          duration: "1.5 hours",
          description: `Taste celebrated local delicacies and traditional culinary specialties in ${cityName}.`,
          image_url: "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=400&q=80"
        },
        {
          name: `Famous Cultural Center / Monument in ${cityName.split(',')[0]}`,
          category: "culture",
          estimated_cost: 200,
          duration: "2 hours",
          description: `Immerse in the historic arts, heritage, and spiritual traditions of ${cityName}.`,
          image_url: "https://images.unsplash.com/photo-1552832230-c0197dd311b5?auto=format&fit=crop&w=400&q=80"
        },
        {
          name: `Scenic Nature Viewpoint & Golden Hour Walk`,
          category: "adventure",
          estimated_cost: 150,
          duration: "2 hours",
          description: `Panoramic vista spot offering scenic skyline and nature photography.`,
          image_url: "https://images.unsplash.com/photo-1533105079780-92b9be482077?auto=format&fit=crop&w=400&q=80"
        },
        {
          name: `Local Artisan Bazaar & Souvenir Shopping`,
          category: "relaxation",
          estimated_cost: 300,
          duration: "2 hours",
          description: `Browse vibrant handicraft markets and regional artisan creations.`,
          image_url: "https://images.unsplash.com/photo-1531572753322-ad063cecc140?auto=format&fit=crop&w=400&q=80"
        },
        {
          name: `Botanical Garden & Waterfront Relaxation`,
          category: "relaxation",
          estimated_cost: 100,
          duration: "1.5 hours",
          description: `Unwind in serene landscaped gardens and open waterfront plazas.`,
          image_url: "https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?auto=format&fit=crop&w=400&q=80"
        }
      ];
    }
  },

  async getSmartBudget(destination, days = 3) {
    try {
      const resp = await fetch(`${API_BASE}/ai/budget/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ destination, days })
      });
      if (resp.ok) {
        return await resp.json();
      }
    } catch (err) {
      console.warn('Smart budget AI fetch notice:', err);
    }

    const total = 3200 * days;
    return {
      destination: destination,
      days: days,
      currency: "INR",
      estimated_total_budget: total,
      breakdown: {
        accommodation: Math.round(total * 0.45),
        food_and_dining: Math.round(total * 0.25),
        activities_and_tours: Math.round(total * 0.18),
        local_transport: Math.round(total * 0.08),
        miscellaneous: Math.round(total * 0.04)
      }
    };
  },

  // ----------------------------------------------------
  // TRIP CREATION & PERSISTENCE
  // ----------------------------------------------------
  async createTripWithAi({ name, destination, startDate, endDate, budget = 15000, description = '' }) {
    let daysCount = 3;
    if (startDate && endDate) {
      const s = new Date(startDate);
      const e = new Date(endDate);
      const diff = Math.ceil((e - s) / (1000 * 60 * 60 * 24)) + 1;
      daysCount = Math.max(1, diff);
    }

    const payload = {
      destination: destination,
      number_of_days: daysCount,
      budget: parseFloat(budget) || 15000
    };

    let aiResult = null;
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 6000);
      const aiResp = await fetch(`${API_BASE}/ai/generate-itinerary/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (aiResp.ok) {
        aiResult = await aiResp.json();
      }
    } catch (e) {
      console.warn('AI endpoint fallback notice:', e);
    }

    try {
      const citiesList = destination.split(',').map(s => s.trim()).filter(Boolean);
      const tripId = Date.now();
      const budgetNum = parseFloat(budget) || 15000;

      const formattedTrip = {
        id: tripId,
        name: name || `Journey across ${destination}`,
        destination: destination,
        cities: citiesList.length ? citiesList : [destination],
        start_date: startDate || new Date().toISOString().split('T')[0],
        end_date: endDate || new Date(Date.now() + daysCount * 86400000).toISOString().split('T')[0],
        duration_days: daysCount,
        estimated_budget: budgetNum,
        budget: budgetNum,
        description: description || `Personalized travel itinerary exploring ${destination}.`,
        currency: "INR",
        status: "Upcoming",
        itineraries: (aiResult && aiResult.days && aiResult.days.length) ? aiResult.days.map((d, idx) => ({
          day_number: d.day || (idx + 1),
          city_name: d.city_name || citiesList[idx % citiesList.length] || destination,
          title: d.theme || `Day ${d.day || (idx + 1)}: ${destination} Exploration`,
          notes: d.notes || `Highlights and sights in ${d.city_name || destination}`,
          allocated_budget: d.allocated_budget || Math.round(budgetNum / daysCount),
          items: (d.activities || []).map(a => ({
            name: a.activity_name || a.name || 'Sightseeing Tour',
            category: a.category || 'sightseeing',
            time: a.time || '09:00 AM',
            estimated_cost: parseFloat(a.estimated_cost) || 200,
            description: a.description || ''
          }))
        })) : []
      };

      if (!formattedTrip.itineraries.length) {
        const acts = await this.fetchActivitiesForCity(destination);
        for (let d = 1; d <= daysCount; d++) {
          const subActs = acts.slice(((d - 1) * 2) % acts.length, (((d - 1) * 2) + 2) % acts.length || acts.length);
          formattedTrip.itineraries.push({
            day_number: d,
            city_name: citiesList[(d - 1) % citiesList.length] || destination,
            title: `Day ${d}: ${citiesList[(d - 1) % citiesList.length] || destination} Highlights`,
            notes: `Full day exploration and sight visits.`,
            allocated_budget: Math.round(budgetNum / daysCount),
            items: subActs.length ? subActs : [
              { name: "Morning City Landmarks Tour", category: "sightseeing", time: "09:00 AM", estimated_cost: 200, description: "Guided exploration of historic center." },
              { name: "Local Culinary & Dining Experience", category: "food", time: "01:30 PM", estimated_cost: 250, description: "Authentic regional lunch." },
              { name: "Sunset Viewpoint & Temple Darshan", category: "culture", time: "06:00 PM", estimated_cost: 150, description: "Evening prayer and panoramic vistas." }
            ]
          });
        }
      }

      let calcTotal = 0;
      formattedTrip.itineraries.forEach(day => {
        (day.items || []).forEach(item => {
          calcTotal += (parseFloat(item.estimated_cost) || 0);
        });
      });
      formattedTrip.total_cost = calcTotal || Math.round(budgetNum * 0.7);

      localStorage.setItem(GT_TRIP_KEY, JSON.stringify(formattedTrip));
      
      const allTrips = this.getAllSavedTrips();
      allTrips.unshift(formattedTrip);
      localStorage.setItem('globetrotter_all_trips', JSON.stringify(allTrips));

      return { success: true, trip: formattedTrip };
    } catch (err) {
      console.error('Trip creation error:', err);
      return { success: false, error: err.message || 'Failed to generate itinerary.' };
    }
  },

  getCurrentTrip() {
    const stored = localStorage.getItem(GT_TRIP_KEY);
    if (stored) {
      try {
        return JSON.parse(stored);
      } catch (e) {}
    }

    const seededTrip = {
      id: 1,
      name: "Divine Coastal Saurashtra: Dwarka & Somnath",
      destination: "Dwarka & Somnath, Gujarat",
      cities: ["Dwarka", "Somnath"],
      start_date: "2026-06-15",
      end_date: "2026-06-18",
      duration_days: 4,
      estimated_budget: 16000,
      budget: 16000,
      total_cost: 2330,
      currency: "INR",
      status: "Ongoing",
      description: "A 4-day pilgrimage and coastal tour covering Dwarkadhish Temple, Bet Dwarka, Nageshwar, and Somnath Jyotirlinga.",
      itineraries: [
        {
          day_number: 1,
          city_name: "Dwarka",
          title: "Dwarka Arrival & Sacred Jagat Mandir Darshan",
          notes: "Morning Mangla Aarti at Dwarkadhish temple followed by Gomti Ghat walk.",
          allocated_budget: 4000,
          flight_or_train: "Express Train: 08:30 AM",
          hotel_name: "Dwarka Heritage Grand",
          items: [
            {
              name: "Dwarkadhish Temple Mangla Darshan",
              category: "culture",
              time: "06:30 AM",
              estimated_cost: 150,
              description: "Sacred darshan at the 5-story ancient temple.",
              image_url: "https://images.unsplash.com/photo-1609766857041-ed402ea8069a?auto=format&fit=crop&w=300&q=80"
            },
            {
              name: "Authentic Gujarati Thali Lunch",
              category: "food",
              time: "01:00 PM",
              estimated_cost: 250,
              description: "Traditional unlimited kathiyawadi lunch with buttermilk."
            },
            {
              name: "Gomti Ghat Sunset & Evening Aarti",
              category: "sightseeing",
              time: "06:30 PM",
              estimated_cost: 50,
              description: "Sunset where Gomti river meets the Arabian Sea."
            }
          ]
        },
        {
          day_number: 2,
          city_name: "Dwarka",
          title: "Bet Dwarka Island & Nageshwar Jyotirlinga",
          notes: "Ferry ride from Okha port to Bet Dwarka.",
          allocated_budget: 4000,
          flight_or_train: "Local Sightseeing Cab: 08:00 AM",
          hotel_name: "Dwarka Heritage Grand",
          items: [
            {
              name: "Bet Dwarka Ferry Boat Ride & Mandir",
              category: "adventure",
              time: "08:30 AM",
              estimated_cost: 300,
              description: "Scenic boat crossing in Gulf of Kutch to the historic island.",
              image_url: "https://images.unsplash.com/photo-1544644181-1484b3fdfc62?auto=format&fit=crop&w=300&q=80"
            },
            {
              name: "Nageshwar Jyotirlinga Temple Visit",
              category: "culture",
              time: "02:30 PM",
              estimated_cost: 100,
              description: "One of the 12 sacred Jyotirlinga shrines."
            },
            {
              name: "Shivrajpur Blue Flag Beach Walk",
              category: "relaxation",
              time: "05:30 PM",
              estimated_cost: 200,
              description: "Pristine white sand certified Blue Flag beach."
            }
          ]
        },
        {
          day_number: 3,
          city_name: "Somnath",
          title: "Transfer to Somnath & First Jyotirlinga Darshan",
          notes: "Scenic coastal highway drive from Dwarka to Somnath.",
          allocated_budget: 4000,
          flight_or_train: "Coastal Highway Coach: 10:15 AM",
          hotel_name: "Somnath Sagar Resort",
          items: [
            {
              name: "Somnath Temple Afternoon Darshan",
              category: "culture",
              time: "03:00 PM",
              estimated_cost: 150,
              description: "Majestic seaside temple honoring the first of twelve Jyotirlingas.",
              image_url: "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&w=300&q=80"
            },
            {
              name: "Somnath Light & Sound Show at Sea Promenade",
              category: "sightseeing",
              time: "07:30 PM",
              estimated_cost: 100,
              description: "Laser and audio presentation on temple history by the sea."
            }
          ]
        },
        {
          day_number: 4,
          city_name: "Somnath",
          title: "Triveni Sangam & Sacred Sites",
          notes: "Morning holy dip and temple darshans.",
          allocated_budget: 4000,
          flight_or_train: "Return Express: 06:00 PM",
          hotel_name: "Somnath Sagar Resort",
          items: [
            {
              name: "Triveni Sangam Holy Dip & Boat Ride",
              category: "adventure",
              time: "08:00 AM",
              estimated_cost: 200,
              description: "Confluence of three holy rivers: Hiran, Kapila, and Saraswati."
            },
            {
              name: "Bhalka Tirth Sacred Visit",
              category: "culture",
              time: "11:30 AM",
              estimated_cost: 80,
              description: "Spot where Lord Krishna concluded his earthly avatar."
            }
          ]
        }
      ]
    };

    localStorage.setItem(GT_TRIP_KEY, JSON.stringify(seededTrip));
    return seededTrip;
  },

  getAllSavedTrips() {
    const stored = localStorage.getItem('globetrotter_all_trips');
    if (stored) {
      try {
        const trips = JSON.parse(stored);
        if (Array.isArray(trips) && trips.length > 0) return trips;
      } catch (e) {}
    }
    const current = this.getCurrentTrip();
    const trips = [
      current,
      {
        id: 2,
        name: "Varanasi Spiritual Ghats & Heritage Trail",
        destination: "Varanasi, Uttar Pradesh",
        cities: ["Varanasi"],
        start_date: "2026-10-10",
        end_date: "2026-10-15",
        duration_days: 5,
        estimated_budget: 14000,
        budget: 14000,
        total_cost: 1850,
        currency: "INR",
        status: "Upcoming",
        description: "Sunrise boat rides at Assi Ghat, Ganga Aarti, and Kashi Vishwanath temple corridor.",
        itineraries: []
      },
      {
        id: 3,
        name: "Manali & Solang Valley Mountain Escape",
        destination: "Manali, Himachal Pradesh",
        cities: ["Manali", "Solang"],
        start_date: "2025-05-02",
        end_date: "2025-05-09",
        duration_days: 7,
        estimated_budget: 22000,
        budget: 22000,
        total_cost: 21500,
        currency: "INR",
        status: "Completed",
        description: "Scenic pine forest trekking, Rohtang pass snow views, and cafe trails in Old Manali.",
        itineraries: []
      }
    ];
    localStorage.setItem('globetrotter_all_trips', JSON.stringify(trips));
    return trips;
  },

  saveCurrentTrip(trip) {
    localStorage.setItem(GT_TRIP_KEY, JSON.stringify(trip));
    const all = this.getAllSavedTrips();
    const idx = all.findIndex(t => t.id === trip.id);
    if (idx !== -1) {
      all[idx] = trip;
    } else {
      all.unshift(trip);
    }
    localStorage.setItem('globetrotter_all_trips', JSON.stringify(all));
  },

  exportTripAsJson(trip) {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(trip, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `GlobeTrotter_${trip.name.replace(/\s+/g, '_')}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  }
};

window.GlobeTrotterAPI = GlobeTrotterAPI;
window.showToast = showToast;
window.setButtonLoading = setButtonLoading;
