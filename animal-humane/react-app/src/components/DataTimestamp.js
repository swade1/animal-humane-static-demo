import React, { useState, useEffect } from 'react';

const DataTimestamp = ({ className = '' }) => {
  const [lastUpdated, setLastUpdated] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTimestamp = async () => {
      try {
        const response = await fetch('/api/last-updated.json');
        if (response.ok) {
          const data = await response.json();
          setLastUpdated(data);
        }
      } catch (error) {
        console.error('Failed to fetch timestamp:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTimestamp();
  }, []);

  if (loading) {
    return <div className={`data-timestamp ${className}`}>Loading timestamp...</div>;
  }

  if (!lastUpdated) {
    return null;
  }

  return (
    <div className={`data-timestamp ${className}`} style={{
      fontSize: '0.85em',
      color: '#666',
      fontStyle: 'italic',
      padding: '4px 8px',
      backgroundColor: '#f8f9fa',
      border: '1px solid #e9ecef',
      borderRadius: '4px',
      display: 'inline-block'
    }}>
      📊 Data last updated: {lastUpdated.human_readable}
    </div>
  );
};

export default DataTimestamp;