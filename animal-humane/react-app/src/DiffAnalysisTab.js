import React, { useEffect, useState } from 'react';
import { fetchDiffAnalysis } from './api';

function DiffAnalysisTab() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadDiffAnalysis = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await fetchDiffAnalysis();
        // Extract data from APIResponse wrapper
        setData(response.data || response);
      } catch (err) {
        setError(err.message);
        console.error('Failed to load diff analysis:', err);
      } finally {
        setLoading(false);
      }
    };

    loadDiffAnalysis();
  }, []);

  if (loading) return <div>Loading diff analysis...</div>;

  if (error) {
    return (
      <div style={{ padding: '20px' }}>
        <div style={{ color: 'red', marginBottom: '10px' }}>
          Error loading diff analysis: {error}
        </div>
        <button onClick={() => window.location.reload()}>
          Retry
        </button>
      </div>
    );
  }

  if (!data) return <div>No data available</div>;

  const renderDogList = (dogs, title) => {
    if (!dogs || dogs.length === 0) {
      return (
        <div style={{ marginBottom: '20px' }}>
          <h3>{title}</h3>
          <p>No dogs in this category</p>
        </div>
      );
    }

    return (
      <div style={{ marginBottom: '20px' }}>
        <h3>{title}</h3>
        {dogs.map((dog, index) => (
          <div key={index} style={{ marginBottom: '5px' }}>
            <a
              href={dog.url || '#'}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: '#007bff', textDecoration: 'none' }}
            >
              {dog.name || 'Unnamed Dog'}
            </a>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2>Dog Movement Analysis</h2>
      <p>This analysis shows changes in dog status between database updates.</p>

      {renderDogList(data.new_dogs, "New Dogs")}
      {renderDogList(data.returned_dogs, "Returned Dogs")}
      {renderDogList(data.adopted_dogs, "Adopted/Reclaimed Dogs")}
      {renderDogList(data.trial_adoption_dogs, "Trial Adoptions")}
      {renderDogList(data.other_unlisted_dogs, "Available but Temporarily Unlisted")}
    </div>
  );
}

export default DiffAnalysisTab;