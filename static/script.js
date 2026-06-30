let map;
window.parkingData = [];
window.markers = {};
let searchAnchor = L.latLng(18.5204, 73.8567); // Default to Pune

// Initialize the map as soon as the page loads
document.addEventListener("DOMContentLoaded", () => {
    const mapContainer = document.getElementById('map');
    if (!mapContainer) return; // Exit if not on map page
    // 1. Initialize map (Centered on Pune as a fallback)
    map = L.map('map').setView([18.5204, 73.8567], 13);
    // 2. Load the free OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    // 3. Fetch parking data from backend
    fetchParkingData();
    // 4. Check for search query in URL
    const urlParams = new URLSearchParams(window.location.search);
    const query = urlParams.get('q');
    
    if (query) {
        document.getElementById('search-input').value = query;
        searchLocation(query);
    } else {
        // 5. Try to get user location
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const userLat = position.coords.latitude;
                    const userLng = position.coords.longitude;
                    searchAnchor = L.latLng(userLat, userLng);
                    
                    // Move map to user and add a blue marker
                    map.setView([userLat, userLng], 14);
                    L.marker([userLat, userLng]).addTo(map)
                        .bindPopup("<b>You are here</b>").openPopup();
                    const statusEl = document.getElementById('status');
                    if (statusEl) statusEl.innerText = "Location found. Showing nearby parking.";
                    renderParkingCards(); // Update list based on new anchor
                },
                () => {
                    if (statusEl) statusEl.innerText = "Using default location.";
                }
            );
        }
    }
});
async function fetchParkingData() {
    try {
        const response = await fetch('/api/parking');
        window.parkingData = await response.json();
        
        window.parkingData.forEach(spot => {
            addParkingMarker(spot);
        });
        renderParkingCards(); // Initial card render
    } catch (error) {
        console.error("Error fetching parking data:", error);
    }
}

function addParkingMarker(spot) {
    const marker = L.marker([spot.lat, spot.lng]).addTo(map);
    window.markers[spot.id] = marker;
    let isTimeValid = true;
    if (spot.available_from && spot.available_to) {
        const now = new Date();
        const from = new Date(spot.available_from);
        const to = new Date(spot.available_to);
        if (now < from || now > to) isTimeValid = false;
    }
    const availableSpaces = spot.available > 0;
    let availabilityClass = 'full';
    let availabilityText = 'Not Available';
    if (isTimeValid && availableSpaces) {
        availabilityClass = 'available';
        availabilityText = 'Available';
    }
    const infoContent = `
        <div class="info-window" style="min-width: 220px; padding: 5px;">
            <h3 style="color: #2c3e50; margin: 0 0 8px 0; font-size: 1.1rem; border-bottom: 2px solid #3498db; padding-bottom: 5px; font-weight: bold;">${spot.name}</h3>
            <p style="margin: 8px 0; font-size: 0.9rem; color: #7f8c8d; line-height: 1.4;">
                <i style="color: #e74c3c;">📍</i> ${spot.address || 'Address not provided'}
            </p>
            <p style="margin: 8px 0; font-size: 0.9rem;">
                <strong>Status:</strong> <span class="${availabilityClass}" style="font-weight: bold; padding: 2px 8px; border-radius: 4px;">${availabilityText}</span>
            </p>
            <div style="display: flex; gap: 8px; margin-top: 15px;">
                <a href="https://www.google.com/maps/dir/?api=1&destination=${spot.lat},${spot.lng}" 
                   target="_blank" 
                   style="flex: 1; background: #3498db; color: white; text-decoration: none; text-align: center; padding: 10px 5px; border-radius: 6px; font-size: 0.85rem; font-weight: bold; transition: background 0.2s;">
                   Navigate
                </a>
                <a href="/spot/${spot.id}" 
                   style="flex: 1; background: #2ecc71; color: white; text-decoration: none; text-align: center; padding: 10px 5px; border-radius: 6px; font-size: 0.85rem; font-weight: bold; transition: background 0.2s;">
                   View Spot
                </a>
            </div>
        </div>
    `;
    marker.bindPopup(infoContent);
}

// Handle the booking action
async function bookSpot(spotId) {
    const vehicleType = document.getElementById(`vehicle-${spotId}`).value;
    const startTimeStr = document.getElementById(`start-${spotId}`).value;
    const endTimeStr = document.getElementById(`end-${spotId}`).value;
    if (!startTimeStr || !endTimeStr) {
        alert("Please select both a start and end time.");
        return;
    }
    const start = new Date(startTimeStr);
    const end = new Date(endTimeStr);
    if (end <= start) {
        alert("End time must be precisely after the start time.");
        return;
    }
    // Calculate duration in hours, rounded up to the nearest whole hour.
    let durationHours = Math.ceil((end - start) / (1000 * 60 * 60));
    if (durationHours < 1) durationHours = 1;
    try {
        const response = await fetch(`/api/book/${spotId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                vehicle_type: vehicleType,
                duration: durationHours,
                start_time: startTimeStr,
                end_time: endTimeStr
            })
        });
        const result = await response.json();
        if (response.ok && result.success) {
            alert(result.message);
            // Redirect to dashboard to show in "My Bookings"
            window.location.href = '/dashboard';
        } else {
            alert(result.message || "Failed to book spot.");
            if (response.status === 401) {
                // Redirect to login if unauthorized
                window.location.href = '/login';
            }
        }
    } catch (error) {
        console.error("Error booking spot:", error);
        alert("An error occurred while trying to book. Please try again.");
    }
}

// Nominatim OpenStreetMap Search
async function searchLocation(queryOverride) {
    const query = queryOverride || document.getElementById('search-input').value;
    if (!query) return;
    // If we're on a page without a map (like the home page), redirect to the map page
    if (!map) {
        window.location.href = `/find?q=${encodeURIComponent(query)}`;
        return;
    }
    const statusEl = document.getElementById('status');
    if (statusEl) statusEl.innerText = "Searching...";
    try {
        const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`);
        const data = await response.json();
        if (data && data.length > 0) {
            const result = data[0];
            const lat = parseFloat(result.lat);
            const lon = parseFloat(result.lon);
            searchAnchor = L.latLng(lat, lon);
            map.setView([lat, lon], 14);
            if (statusEl) statusEl.innerText = `Moved map to ${query}.`;
            renderParkingCards(); // Update list based on new anchor
        } else {
            alert("Location not found.");
            if (statusEl) statusEl.innerText = "Location not found.";
        }
    } catch (error) {
        console.error("Search error:", error);
        if (statusEl) statusEl.innerText = "Search error.";
    }
}

// Dynamically Render List Cards Sorting By Map Center
function renderParkingCards() {
    const container = document.getElementById('parking-list-container');
    if (!container || !window.parkingData || !map) return; 
    // Use the searchAnchor if available, otherwise fallback to map center
    const center = searchAnchor || map.getCenter();
    const RADIUS_METERS = 15000; // 15km radius filter
    // Compute raw geographic distances to the ANCHOR, filter by radius, and sort
    const nearbySpots = window.parkingData
        .map(spot => {
            const dist = map.distance(center, L.latLng(spot.lat, spot.lng));
            return { ...spot, distance: dist };
        })
        .filter(spot => spot.distance <= RADIUS_METERS)
        .sort((a, b) => a.distance - b.distance);
    container.innerHTML = ''; // clear
    if (nearbySpots.length === 0) {
        container.innerHTML = `
            <div style="padding: 40px 20px; text-align: center; color: #7f8c8d;">
                <i style="font-size: 3rem; display: block; margin-bottom: 10px; opacity: 0.5;">📍</i>
                <p>No parking spots found within 15km of this location.</p>
                <p style="font-size: 0.9rem; margin-top: 10px;">Try searching for another area or zoom out.</p>
            </div>
        `;
        return;
    }
    nearbySpots.forEach(spot => {
        let isTimeValid = true;
        if (spot.available_from && spot.available_to) {
            const now = new Date();
            const from = new Date(spot.available_from);
            const to = new Date(spot.available_to);
            if (now < from || now > to) isTimeValid = false;
        }
        const availableSpaces = spot.available > 0;
        let availabilityText = 'Available';
        let statusColor = '#27ae60';
        if (!isTimeValid) {
            availabilityText = 'Unavailable (Closed)';
            statusColor = '#e74c3c';
        } else if (!availableSpaces) {
            availabilityText = 'Full';
            statusColor = '#e67e22';
        } else {
            availabilityText = `${spot.available} spots left`;
        }
        const imgUrl = (spot.images && spot.images.length > 0) 
            ? `/static/uploads/${spot.images[0]}` 
            : 'https://placehold.co/600x400?text=No+Image';
        const card = document.createElement('div');
        card.className = 'parking-card';
        card.onclick = () => viewOnMap(spot.id, spot.lat, spot.lng);
        card.innerHTML = `
            <img src="${imgUrl}" alt="${spot.name}">
            <div class="parking-card-content">
                <div class="parking-card-header">
                    <h3>${spot.name}</h3>
                    <p class="address">📍 ${spot.address || 'Address not provided'}</p>
                </div>
                <div class="parking-card-info">
                    <p class="price">₹${spot.price_per_hour}<span>/hr</span></p>
                    <span class="status-badge" style="color: ${statusColor};">${availabilityText}</span>
                </div>
                <div class="parking-card-actions">
                    <button onclick="event.stopPropagation(); window.location.href='/spot/${spot.id}'" class="btn-view">View Details</button>
                    <button onclick="event.stopPropagation(); viewOnMap(${spot.id}, ${spot.lat}, ${spot.lng})" class="btn-map">On Map</button>
                </div>
            </div>
        `;
        container.appendChild(card);
    });
}

function viewOnMap(id, lat, lng) {
    if (map) {
        window.scrollTo({ top: 0, behavior: 'smooth' });
        map.flyTo([lat, lng], 16);
        setTimeout(() => {
            if (window.markers[id]) {
                window.markers[id].openPopup();
            }
        }, 600); // give the map time to fly
    }
}

// Header scroll effect and mobile menu toggle
document.addEventListener("DOMContentLoaded", () => {
    const header = document.getElementById('main-header');
    const menuToggle = document.getElementById('menu-toggle');
    const navLinks = document.getElementById('nav-links');
    if (header) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
        });
    }
    if (menuToggle && navLinks) {
        menuToggle.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            // Animate hamburger to X
            const spans = menuToggle.querySelectorAll('span');
            if (navLinks.classList.contains('active')) {
                spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
                spans[1].style.opacity = '0';
                spans[2].style.transform = 'rotate(-45deg) translate(7px, -7px)';
            } else {
                spans[0].style.transform = 'none';
                spans[1].style.opacity = '1';
                spans[2].style.transform = 'none';
            }
        });
        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!menuToggle.contains(e.target) && !navLinks.contains(e.target)) {
                if (navLinks.classList.contains('active')) {
                    navLinks.classList.remove('active');
                    const spans = menuToggle.querySelectorAll('span');
                    spans[0].style.transform = 'none';
                    spans[1].style.opacity = '1';
                    spans[2].style.transform = 'none';
                }
            }
        });
    }
});

// Intersection Observer for scroll reveal animations
document.addEventListener('DOMContentLoaded', () => {
    const observerOptions = { threshold: 0.15 };
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => { if (entry.isIntersecting) entry.target.classList.add('active'); });
    }, observerOptions);
    document.querySelectorAll('.reveal, .reveal-left, .reveal-right').forEach(el => observer.observe(el));
});

function switchHeroTab(tab) {
    const tabFind = document.getElementById('tab-find');
    const tabRent = document.getElementById('tab-rent');
    const contentFind = document.getElementById('content-find');
    const contentRent = document.getElementById('content-rent');
    const heroWrapper = document.getElementById('hero-wrapper');
    
    if (!tabFind || !tabRent || !contentFind || !contentRent) return;
    
    if (tab === 'find') {
        tabFind.classList.add('active'); 
        tabRent.classList.remove('active');
        contentFind.style.display = 'block'; 
        contentRent.style.display = 'none';
        if (heroWrapper) {
            heroWrapper.style.backgroundImage = "linear-gradient(rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.1)), url('/static/find_bg.png')";
        }
    } else {
        tabRent.classList.add('active'); 
        tabFind.classList.remove('active');
        contentRent.style.display = 'block'; 
        contentFind.style.display = 'none';
        if (heroWrapper) {
            heroWrapper.style.backgroundImage = "linear-gradient(rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.1)), url('/static/rent_bg.png')";
        }
    }
}
