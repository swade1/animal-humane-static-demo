import React, { useState, useEffect } from 'react';
import { getApiMode } from '../api.js';

const DemoBanner = () => {
  const [apiMode, setApiMode] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    // Get API mode info
    setApiMode(getApiMode());

    // Fetch last updated timestamp
    const fetchTimestamp = async () => {
      try {
        const response = await fetch('/api/last-updated.json');
        if (response.ok) {
          const data = await response.json();
          setLastUpdated(data);
        }
      } catch (error) {
        console.error('Failed to fetch timestamp:', error);
      }
    };

    fetchTimestamp();
  }, []);

  // Only show banner in static mode
  if (!apiMode?.isStatic) {
    return null;
  }

  const displayDate = lastUpdated ? 
    new Date(lastUpdated.timestamp * 1000).toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    }) : 
    'January 1, 2026';

  return (
    <div style={{
      backgroundColor: '#e8f4f8',
      border: '1px solid #bee5eb',
      borderRadius: '4px',
      padding: '12px 16px',
      margin: '16px 0',
      textAlign: 'center',
      fontSize: '0.95em',
      color: '#0c5460'
    }}>
      <div style={{ fontWeight: '600', marginBottom: '4px' }}>
        🎯 Portfolio Demo
      </div>
      <div>
        This is a static demonstration using data from <strong>{displayDate}</strong>
      </div>
      <div style={{ fontSize: '0.85em', marginTop: '4px', opacity: 0.8 }}>
        Data updates every 2 hours via automated GitHub Actions
      </div>
    </div>
  );
};

export default DemoBanner;