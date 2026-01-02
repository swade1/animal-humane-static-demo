// api.js

// Static mode detection - checks if we're running in static demo mode
const isStaticMode = () => {
  // Force static mode if REACT_APP_STATIC_DEMO is set
  if (process.env.REACT_APP_STATIC_DEMO === 'true') {
    return true;
  }
  
  // Auto-detect: if not on development port, assume static mode
  return window.location.hostname !== 'localhost' || 
         window.location.port === '3000' ||
         !window.location.port;
};

// Base URL configuration - uses relative paths for static files when in static mode
const API_BASE = isStaticMode() ? "/api" : "/api"; // Both use relative paths now

// Simple error handling function
const handleResponse = async (response) => {
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HTTP ${response.status}: ${errorText}`);
  }
  return await response.json();
};

// Fetch all dogs (for listing/editing)
export async function fetchDogs() {
  try {
    const response = await fetch(`${API_BASE}/dogs`);
    return await handleResponse(response);
  } catch (error) {
    console.error('Failed to fetch dogs:', error);
    throw error;
  }
}

// Fetch one dog by ID (for editing)
export async function fetchDogById(dogId) {
  try {
    const response = await fetch(`${API_BASE}/dogs/${dogId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch dog ${dogId}: ${response.status} ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error(error);
    throw error;
  }
}

// Update dog document by ID with partial fields
export async function updateDog(dogId, updateData) {
  console.log("updateData passed to updateDog is:", updateData);  
  console.log(`${API_BASE}/dogs/${dogId}`)
  const response = await fetch(`${API_BASE}/dogs/${dogId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updateData),
  });
  if (!response.ok) throw new Error(`Failed to update dog ${dogId}`);
  return await response.json();
}

export async function fetchLatestIndex(dogId) {
  try {
      const res = await fetch(`/api/dogs/${dogId}/latest_index`);
      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Failed to fetch latest index: ${res.status} ${res.statusText} - ${errorText}`);
      }
      return res.json();
    } catch (error) {
      console.error("fetchLatestIndex error:", error);
      throw error;
    }
}

// Makes a fetch GET request to your backend endpoint for document updates
export async function runDocumentUpdates() {
  const response = await fetch('/animal_updates_text', {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    }
    // No body needed if your endpoint doesn’t require additional data
  });

  if (!response.ok) {
    throw new Error('API request failed');
  }

  return response.text();
}

// Fetch overview statistics for the shelter dashboard
export async function fetchOverviewStats() {
  const endpoint = isStaticMode() ? '/api/overview.json' : '/api/overview';
  const res = await fetch(endpoint);
  if (!res.ok) {
    throw new Error('Failed to fetch overview stats');
  }
  return res.json();
}

// Fetch live population data of animals currently in the shelter
export async function fetchLivePopulation() {
  const endpoint = isStaticMode() ? '/api/live-population.json' : '/api/live_population';
  const res = await fetch(endpoint);
  if (!res.ok) {
    throw new Error('Failed to fetch live population');
  }
  return res.json();
}

// Fetch recent adoption movement events (adopted, returned, trial)
export async function fetchAdoptions() {
  const endpoint = isStaticMode() ? '/api/adoptions.json' : '/api/adoptions';
  const res = await fetch(endpoint);

  if (!res.ok) {
    throw new Error('Failed to fetch adoption movement');
  }
  return res.json();
}

// Fetch insights & spotlight data for advanced analytics and reporting
export async function fetchInsights() {
  const endpoint = isStaticMode() ? '/api/insights.json' : '/api/insights';
  const res = await fetch(endpoint);
  if (!res.ok) {
    throw new Error('Failed to fetch insights');
  }
  return res.json();
}

// Fetch length of stay histogram data
export async function fetchLengthOfStayData() {
  const endpoint = isStaticMode() ? '/api/length-of-stay.json' : '/api/length-of-stay';
  const response = await fetch(endpoint);
  if (!response.ok) throw new Error('Failed to fetch length of stay data');
  return response.json();
}
export async function fetchWeeklyAgeGroupAdoptions() {
  const endpoint = isStaticMode() ? '/api/weekly-age-group-adoptions.json' : '/api/weekly-age-group-adoptions';
  const response = await fetch(endpoint);
  if (!response.ok) throw new Error('Failed to fetch weekly age group adoptions');
  return response.json();
}

export async function fetchDogOrigins() {
  console.log("fetchDogOrigins called");
  const endpoint = isStaticMode() ? '/api/dog-origins.json' : '/api/dog-origins';
  const response = await fetch(endpoint);
  if (!response.ok) throw new Error('Failed to fetch dog origins');
  return await response.json();
}

export async function fetchDiffAnalysis() {
  const endpoint = isStaticMode() ? '/api/diff-analysis.json' : '/api/diff-analysis';
  const response = await fetch(endpoint);
  if (!response.ok) throw new Error('Failed to fetch diff analysis');
  return response.json();
}

export async function fetchRecentPupdates() {
  const endpoint = isStaticMode() ? '/api/recent-pupdates.json' : '/api/recent-pupdates';
  const response = await fetch(endpoint);
  if (!response.ok) throw new Error('Failed to fetch recent pupdates');
  return response.json();
}

// Clear API cache
export async function clearCache() {
  // In static mode, cache clearing is not applicable
  if (isStaticMode()) {
    console.log('[STATIC MODE] Cache clearing not available in static demo');
    return { message: 'Cache clearing not available in static demo mode', static_demo: true };
  }
  
  const res = await fetch('/api/cache/clear', { method: 'POST' });
  if (!res.ok) {
    throw new Error('Failed to clear cache');
  }
  return res.json();
}

// Utility function to check current API mode
export function getApiMode() {
  return {
    isStatic: isStaticMode(),
    baseUrl: API_BASE,
    environment: process.env.NODE_ENV,
    hostname: window.location.hostname,
    port: window.location.port
  };
}

// Log current API configuration on load
if (isStaticMode()) {
  console.log('[STATIC DEMO MODE] Using static JSON files for API responses');
} else {
  console.log('[LIVE MODE] Using backend API endpoints');
}


