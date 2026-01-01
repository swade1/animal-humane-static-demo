// api.js

const API_BASE = "/api"; // Base URL prefix for your backend API

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
  const res = await fetch('/api/overview');
  if (!res.ok) {
    throw new Error('Failed to fetch overview stats');
  }
  return res.json();
}

// Fetch live population data of animals currently in the shelter
export async function fetchLivePopulation() {
  const res = await fetch('/api/live_population');
  if (!res.ok) {
    throw new Error('Failed to fetch live population');
  }
  return res.json();
}

// Fetch recent adoption movement events (adopted, returned, trial)
export async function fetchAdoptions() {
  const res = await fetch('/api/adoptions');

  if (!res.ok) {
    throw new Error('Failed to fetch adoption movement');
  }
  return res.json();
}

// Fetch insights & spotlight data for advanced analytics and reporting
export async function fetchInsights() {
  const res = await fetch('/api/insights');
  if (!res.ok) {
    throw new Error('Failed to fetch insights');
  }
  return res.json();
}

// Fetch length of stay histogram data
export async function fetchLengthOfStayData() {
  const response = await fetch('/api/length-of-stay');
  if (!response.ok) throw new Error('Failed to fetch length of stay data');
  return response.json();
}
export async function fetchWeeklyAgeGroupAdoptions() {
  const response = await fetch('/api/weekly-age-group-adoptions');
  if (!response.ok) throw new Error('Failed to fetch weekly age group adoptions');
  return response.json();
}

export async function fetchDogOrigins() {
  console.log("fetchDogOrigins called");
  const response = await fetch('/api/dog-origins');
  if (!response.ok) throw new Error('Failed to fetch dog origins');
  return await response.json();
}

export async function fetchDiffAnalysis() {
  const response = await fetch('/api/diff-analysis');
  if (!response.ok) throw new Error('Failed to fetch diff analysis');
  return response.json();
}

export async function fetchRecentPupdates() {
  const response = await fetch('/api/recent-pupdates');
  if (!response.ok) throw new Error('Failed to fetch recent pupdates');
  return response.json();
}

// Clear API cache
export async function clearCache() {
  const res = await fetch('/api/cache/clear', { method: 'POST' });
  if (!res.ok) {
    throw new Error('Failed to clear cache');
  }
  return res.json();
}


