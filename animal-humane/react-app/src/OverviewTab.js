import React, { useEffect, useState } from 'react';
import { fetchOverviewStats } from './api';

function OverviewTab() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadStats = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await fetchOverviewStats();
        // Extract data from APIResponse wrapper
        setStats(response.data || response);
      } catch (err) {
        setError(err.message);
        console.error('Failed to load overview stats:', err);
      } finally {
        setLoading(false);
      }
    };

    loadStats();
  }, []);

  if (loading) return <div>Loading overview statistics...</div>;
  
  if (error) {
    return (
      <div style={{ padding: '20px' }}>
        <div style={{ color: 'red', marginBottom: '10px' }}>
          Error loading overview: {error}
        </div>
        <button onClick={() => window.location.reload()}>
          Retry
        </button>
      </div>
    );
  }

  if (!stats) return <div>No data available</div>;



  const ageOrder = ["Puppy","Adult","Senior"];

  const labelMap = {
    "Puppy":"Puppies (0 to 1 year):",
    "Adult":"Adults:",
    "Senior":"Seniors (8+ years):"
  };

  const sortedAgeGroups = stats.ageGroups
    ? [...stats.ageGroups].sort((a, b) => {
        return ageOrder.indexOf(a.age_group) - ageOrder.indexOf(b.age_group);
      })
    : [];

  // Replace objects below with your fields and structure
  return (
    <div>
      <div>
      <h3 style={{ marginTop: '10px', textAlign: 'center' }}>Shelter Overview</h3>
      <table style={{ width: "50%", marginTop: "16px", textAlign: "left", borderCollapse: "collapse" }}>
        <tbody>
          <tr>
            <td><strong>Dogs in Shelter:</strong></td>
            <td>{stats.total}</td>
          </tr><br />
          <tr>
            <td><strong>New this week:</strong></td>
            <td>{stats.newThisWeek}</td>
          </tr><br />
          <tr>
            <td><strong>Adopted this week:</strong></td>
            <td>{stats.adoptedThisWeek}</td>
          </tr><br />
          <tr>
            <td><strong>Trial Adoptions:</strong></td>
            <td>{stats.trialAdoptions}</td>
          </tr><br />
          <tr>
            <td><strong>Average Length of Stay:</strong></td>
            <td>{stats.avgStay} days</td>
          </tr><br />
          <tr>
            <td><strong>Longest Stay:</strong></td>
            <td>{stats.longestStay.days} days (<a
              href={stats.longestStay.url}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: "#2a5db0", textDecoration: "underline" }}
            >
              {stats.longestStay.name}
            </a>)
          </td>
          </tr><br />
          <tr>
            <td style={{ verticalAlign: "top" }}>
              <strong>Available Dogs by Age Group:</strong>
            </td>
            <td>
              <table style={{ marginLeft: "0", borderCollapse: "separate", borderSpacing: "10px 4px" }}>
                <tbody>
                  {sortedAgeGroups.map(item =>
                    labelMap[item.age_group] ? (
                      <tr key={item.age_group}>
                        <td style={{padding: "4px 20px", textAlign:"left"}}>
                            {labelMap[item.age_group]}
                        </td>
                        <td style={{padding: "4px 20px", textAlign:"right"}}>
                          {item.count}
                        </td>
                      </tr>
                    ) : null
                  )}
                </tbody>
              </table>
            </td>
          </tr>
        </tbody>
      </table>
    </div>


      {/* Add trend, alerts, small charts here */}
    </div>
  );
}

export default OverviewTab;

